import uuid, random, asyncio, json, os
from typing import Dict, List, Optional
import time # Added for timestamp in history

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------- Card helpers ----------
VALUE_MAP = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
             "7": 7, "8": 8, "9": 9, "T": 10, "J": 11, "Q": 12, "K": 13}
SUITS = "CDHS"  # clubs, diamonds, hearts, spades

# Persistence file
GAME_STATE_FILE = "game_state.json"

def fresh_deck() -> List[str]:
    return [rank + suit for rank in VALUE_MAP for suit in SUITS]


def card_value(card: str) -> int:
    return VALUE_MAP[card[0]]

# ---------- Core domain -------------------------------------------------------


class Player:
    def __init__(self, pid: str, name: str, seat: int, stack: int, buy_in: int = None):
        self.pid = pid
        self.name = name
        self.seat = seat
        self.stack = stack
        self.buy_in = buy_in if buy_in is not None else stack  # Track original buy-in
        self.pnl = 0
        self.cards: List[str] = []
        self.status = "active"          # 'active', 'away', 'leaving', 'pending_away', 'pending_leaving', 'left'
        self.last_seen = None  # For tracking disconnections

    # info visible to clients
    def to_public(self, reveal_cards: bool):
        data = {
            "pid": self.pid,
            "name": self.name,
            "seat": self.seat,
            "stack": self.stack,
            "buy_in": self.buy_in,
            "pnl": self.pnl,
            "status": self.status,
        }
        if reveal_cards:
            data["cards"] = self.cards
        return data

    def to_dict(self):
        """Serialize player for persistence"""
        return {
            "pid": self.pid,
            "name": self.name,
            "seat": self.seat,
            "stack": self.stack,
            "buy_in": self.buy_in,
            "pnl": self.pnl,
            "cards": self.cards,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize player from persistence"""
        player = cls(data["pid"], data["name"], data["seat"], data["stack"], data.get("buy_in", data["stack"]))
        player.pnl = data.get("pnl", 0)
        player.cards = data.get("cards", [])
        player.status = data.get("status", "active")
        return player


class Table:
    def __init__(self, tid: str):
        self.tid = tid
        self.players: Dict[str, Player] = {}
        self.seat_order: List[str] = []   # maintain rotation order
        self.maker_idx = 0

        self.deck: List[str] = fresh_deck()
        random.shuffle(self.deck)
        self.community: List[str] = []

        self.round_num = 0               # 0‑based, 0‑3 (after 4th round settlement)
        self.trades: List[dict] = []
        self.quotes: List[dict] = []     # list of {bid,ask,round}
        self.round_trades: List[str] = []  # player IDs who have traded this round
        
        # Game history - stores completed hands
        self.hand_number = 0
        self.game_history: List[dict] = []  # [{hand_number, trades, quotes, final_total, settlements}]
        self.max_history_hands = 100  # Limit to prevent memory bloat
        
        # Keep track of players who have left (for leaderboard/history)
        self.left_players: Dict[str, Player] = {}  # pid -> Player (preserves their final state)

        self.lock = asyncio.Lock()

    def to_dict(self):
        """Serialize table for persistence"""
        return {
            "tid": self.tid,
            "players": {pid: player.to_dict() for pid, player in self.players.items()},
            "seat_order": self.seat_order,
            "maker_idx": self.maker_idx,
            "deck": self.deck,
            "community": self.community,
            "round_num": self.round_num,
            "trades": self.trades,
            "quotes": self.quotes,
            "round_trades": self.round_trades,
            "hand_number": self.hand_number,
            "game_history": self.game_history,
            "max_history_hands": self.max_history_hands,
            "left_players": {pid: player.to_dict() for pid, player in self.left_players.items()}
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize table from persistence"""
        table = cls(data["tid"])
        table.players = {pid: Player.from_dict(pdata) for pid, pdata in data.get("players", {}).items()}
        table.seat_order = data.get("seat_order", [])
        table.maker_idx = data.get("maker_idx", 0)
        table.deck = data.get("deck", fresh_deck())
        table.community = data.get("community", [])
        table.round_num = data.get("round_num", 0)
        table.trades = data.get("trades", [])
        table.quotes = data.get("quotes", [])
        table.round_trades = data.get("round_trades", [])
        table.hand_number = data.get("hand_number", 0)
        table.game_history = data.get("game_history", [])
        table.max_history_hands = data.get("max_history_hands", 100)
        table.left_players = {pid: Player.from_dict(pdata) for pid, pdata in data.get("left_players", {}).items()}
        return table

    # ---- gameplay state helpers ---------------------------------------------

    def maker_pid(self) -> Optional[str]:
        if not self.seat_order:
            return None
        return self.seat_order[self.maker_idx]

    # ---- flow control --------------------------------------------------------

    def new_hand(self):
        # Save completed hand to history before clearing
        if self.trades or self.quotes:  # Only save if there was activity
            hand_record = {
                "hand_number": self.hand_number,
                "trades": self.trades.copy(),
                "quotes": self.quotes.copy(),
                "final_total": self.evaluate_total() if self.round_num >= 4 else None,
                "maker": self.maker_pid(),
                "timestamp": time.time()
            }
            self.game_history.append(hand_record)
            
            # Limit history size to prevent memory bloat
            if len(self.game_history) > self.max_history_hands:
                self.game_history.pop(0)  # Remove oldest hand
        
        # Process pending statuses before starting new hand
        players_to_remove = []
        leaving_players = []  # Track players who are leaving for event notifications
        
        for pid, p in self.players.items():
            if p.status == "pending_away":
                p.status = "away"
                print(f"Player {p.name} is now away (was pending)")
            elif p.status == "pending_leaving":
                # Store info before removal for events
                leaving_players.append({"pid": pid, "name": p.name, "seat": p.seat})
                # Move player to left_players and mark for removal
                p.status = "left"
                self.left_players[pid] = p
                players_to_remove.append(pid)
                print(f"Player {p.name} has left the table (was pending)")
        
        # Remove players who are leaving
        for pid in players_to_remove:
            del self.players[pid]
            # Remove from seat order
            if pid in self.seat_order:
                self.seat_order.remove(pid)
            # Adjust maker index if needed
            if self.seat_order and self.maker_idx >= len(self.seat_order):
                self.maker_idx = 0
        
        # Clear current hand data
        self.hand_number += 1
        self.deck = fresh_deck()
        random.shuffle(self.deck)
        self.community.clear()
        self.round_num = 0
        self.trades.clear()
        self.quotes.clear()
        self.round_trades.clear()
        for p in self.players.values():
            p.cards = [self.deck.pop(), self.deck.pop()]
        
        # Return info about players who left for event handling
        return leaving_players

    def next_round(self):
        if self.round_num < 3:            # reveal exactly three community cards total
            self.community.append(self.deck.pop())
        self.round_num += 1
        self.round_trades.clear()  # Reset trades for new round

    def rotate_maker(self):
        if self.seat_order:
            self.maker_idx = (self.maker_idx + 1) % len(self.seat_order)

    # ---- settlement ----------------------------------------------------------

    def evaluate_total(self) -> int:
        total = sum(card_value(c) for c in self.community)
        for p in self.players.values():
            total += sum(card_value(c) for c in p.cards)
        return total

    def settle(self):
        total = self.evaluate_total()
        print(f"Settlement: Total card value = {total}")
        
        maker_pnl = 0  # Track total PnL for market maker
        
        # Calculate P&L for each trade and update player balances
        for tr in self.trades:  # {pid, side, price}
            if tr["pid"] not in self.players:
                continue  # Skip if player no longer exists
                
            player = self.players[tr["pid"]]
            diff = total - tr["price"]
            pnl = diff if tr["side"] == "buy" else -diff
            
            print(f"Player {player.name}: {tr['side']} at {tr['price']}, total={total}, diff={diff}, pnl={pnl}")
            
            # Update player's P&L and stack
            player.pnl += pnl
            player.stack += pnl
            
            # Market maker gets the opposite PnL from each trade
            maker_pnl -= pnl
            
            # If stack goes negative, player is eliminated (optional - can be removed)
            if player.stack < 0:
                player.status = "eliminated"
        
        # Update market maker's PnL
        maker_id = self.maker_pid()
        if maker_id and maker_id in self.players:
            maker = self.players[maker_id]
            print(f"Market Maker {maker.name}: total PnL from trades = {maker_pnl}")
            maker.pnl += maker_pnl
            maker.stack += maker_pnl
            
            if maker.stack < 0:
                maker.status = "eliminated"
        else:
            print(f"Warning: No market maker found or maker not in players. maker_id={maker_id}")
    
    def all_players_traded_this_round(self) -> bool:
        """Check if all active players have traded in the current round"""
        # Include active, pending_away, and pending_leaving players (they're still playing this hand)
        active_players = [pid for pid, p in self.players.items() if p.status in ["active", "pending_away", "pending_leaving"]]
        # Exclude the maker from needing to trade
        non_maker_players = [pid for pid in active_players if pid != self.maker_pid()]
        
        current_round_trades = [pid for pid in self.round_trades if pid in non_maker_players]
        return len(current_round_trades) >= len(non_maker_players)

    def get_recent_history(self, num_hands: int = 10) -> List[dict]:
        """Get recent game history for frontend display"""
        return self.game_history[-num_hands:] if self.game_history else []

    def get_session_stats(self) -> dict:
        """Get session-wide statistics"""
        if not self.game_history:
            return {"hands_played": 0, "total_trades": 0, "avg_spread": 0}
        
        total_trades = sum(len(hand["trades"]) for hand in self.game_history)
        total_quotes = sum(len(hand["quotes"]) for hand in self.game_history)
        
        # Calculate average spread
        all_quotes = []
        for hand in self.game_history:
            all_quotes.extend(hand["quotes"])
        
        avg_spread = 0
        if all_quotes:
            spreads = [q["ask"] - q["bid"] for q in all_quotes if "bid" in q and "ask" in q]
            avg_spread = sum(spreads) / len(spreads) if spreads else 0
        
        return {
            "hands_played": len(self.game_history),
            "total_trades": total_trades,
            "total_quotes": total_quotes,
            "avg_spread": round(avg_spread, 2)
        }

    def get_all_players_for_leaderboard(self) -> List[dict]:
        """Get all players (active + left) for leaderboard display"""
        all_players = []
        
        # Add current players
        for p in self.players.values():
            all_players.append(p.to_public(reveal_cards=False))
        
        # Add left players
        for p in self.left_players.values():
            player_data = p.to_public(reveal_cards=False)
            player_data["has_left"] = True  # Mark as left for frontend
            all_players.append(player_data)
        
        return all_players

# ---------- Persistence helpers ----------------------------------------------

def save_game_state(tables: Dict[str, Table]):
    """Save game state to file"""
    try:
        data = {tid: table.to_dict() for tid, table in tables.items()}
        with open(GAME_STATE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving game state: {e}")

def load_game_state() -> Dict[str, Table]:
    """Load game state from file"""
    try:
        if os.path.exists(GAME_STATE_FILE):
            with open(GAME_STATE_FILE, 'r') as f:
                data = json.load(f)
            return {tid: Table.from_dict(tdata) for tid, tdata in data.items()}
    except Exception as e:
        print(f"Error loading game state: {e}")
    return {}

# ---------- Connection manager -----------------------------------------------


class ConnectionManager:
    def __init__(self):
        self.websockets: Dict[str, WebSocket] = {}   # pid -> socket
        self.player_table: Dict[str, str] = {}       # pid -> tid

    async def connect(self, pid: str, tid: str, websocket: WebSocket):
        await websocket.accept()
        self.websockets[pid] = websocket
        self.player_table[pid] = tid

    def disconnect(self, pid: str):
        self.websockets.pop(pid, None)
        self.player_table.pop(pid, None)
    
    def update_player_id(self, old_pid: str, new_pid: str):
        """Update player ID when transitioning from temporary to real ID"""
        if old_pid in self.websockets:
            self.websockets[new_pid] = self.websockets.pop(old_pid)
        if old_pid in self.player_table:
            self.player_table[new_pid] = self.player_table.pop(old_pid)

    async def send_personal(self, pid: str, payload: dict):
        ws = self.websockets.get(pid)
        if ws:
            try:
                await ws.send_json(payload)
            except:
                # Connection lost, clean up
                self.disconnect(pid)

    async def broadcast_table(self, table: Table, payload: dict):
        disconnected = []
        for pid in table.players:
            ws = self.websockets.get(pid)
            if ws:
                try:
                    await ws.send_json(payload)
                except:
                    disconnected.append(pid)
        
        # Clean up disconnected players
        for pid in disconnected:
            self.disconnect(pid)

    async def broadcast_all_states(self, table: Table, include_recent_history: bool = False):
        """Send personalized state to all connected players"""
        # Send to all players who are connected (including those who just joined)
        for pid, ws in self.websockets.items():
            # Check if this connection should receive this table's updates
            if self.player_table.get(pid) == table.tid:
                # Only reveal cards to the player themselves
                reveal_pid = pid if pid in table.players else None
                
                state = {
                    "type": "state",
                    "round": table.round_num,
                    "community": table.community,
                    "players": [
                        p.to_public(reveal_cards=(p.pid == reveal_pid))
                        for p in table.players.values()
                    ],
                    "all_players": table.get_all_players_for_leaderboard(),  # Include left players for leaderboard
                    "maker": table.maker_pid(),
                    "quotes": table.quotes,
                    "trades": table.trades,
                    "hand_number": table.hand_number,
                }
                
                # Optionally include recent history (e.g., for game log)
                if include_recent_history:
                    state["recent_history"] = table.get_recent_history(5)  # Last 5 hands
                    state["session_stats"] = table.get_session_stats()
                
                try:
                    await ws.send_json(state)
                except:
                    pass

# ---------- FastAPI setup ----------------------------------------------------


app = FastAPI(title="Market Maker Game", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load existing game state on startup
# Start fresh each time - don't load previous game state
tables: Dict[str, Table] = {}
manager = ConnectionManager()

# Clear any existing game state file on startup
try:
    if os.path.exists(GAME_STATE_FILE):
        os.remove(GAME_STATE_FILE)
        print(f"Cleared previous game state: {GAME_STATE_FILE}")
except Exception as e:
    print(f"Warning: Could not clear game state file: {e}")

# ---- REST ­— join -----------------------------------------------------------


# HTTP join models removed - now using WebSocket-based joining


# HTTP join endpoint removed - now using WebSocket-based joining

@app.get("/table/{tid}/history")
async def get_game_history(tid: str, limit: int = 10):
    """Get recent game history for a table"""
    if tid not in tables:
        raise HTTPException(status_code=404, detail="Table not found")
    
    table = tables[tid]
    return {
        "recent_hands": table.get_recent_history(limit),
        "session_stats": table.get_session_stats(),
        "current_hand": table.hand_number
    }

@app.get("/table/{tid}/stats")
async def get_session_stats(tid: str):
    """Get session statistics"""
    if tid not in tables:
        raise HTTPException(status_code=404, detail="Table not found")
    
    table = tables[tid]
    return table.get_session_stats()

# ---- WebSocket ­— gameplay --------------------------------------------------


@app.websocket("/ws/{tid}/{pid}")
async def websocket_endpoint(ws: WebSocket, tid: str, pid: str):
    table = tables.get(tid)
    if not table:
        # Allow connection even if table doesn't exist yet - it might be created soon
        table = Table(tid)
        tables[tid] = table
    
    # Allow connection even if player doesn't exist yet - they might rejoin
    await manager.connect(pid, tid, ws)
    
    # Track current player ID (may change during join)
    current_pid = pid

    async def push_state():
        # Find the current player ID to use for revealing cards
        reveal_pid = current_pid if current_pid in table.players else None
        
        state = {
            "type": "state",
            "round": table.round_num,
            "community": table.community,
            "players": [
                p.to_public(reveal_cards=(p.pid == reveal_pid))  # private cards to self only
                for p in table.players.values()
            ],
            "all_players": table.get_all_players_for_leaderboard(),  # Include left players for leaderboard
            "maker": table.maker_pid(),
            "quotes": table.quotes,
            "trades": table.trades,
            "hand_number": table.hand_number,
        }
        await manager.send_personal(current_pid, state)

    # If player doesn't exist in table, they might be reconnecting or joining for first time
    if current_pid not in table.players:
        # Send a minimal state without player-specific data
        await manager.send_personal(current_pid, {
            "type": "state", 
            "round": table.round_num,
            "community": table.community,
            "players": [p.to_public(reveal_cards=False) for p in table.players.values()],
            "all_players": table.get_all_players_for_leaderboard(),
            "maker": table.maker_pid(),
            "quotes": table.quotes,
            "trades": table.trades,
            "hand_number": table.hand_number,
        })
    else:
        # Player exists - they're reconnecting, mark them as active and update last_seen
        table.players[current_pid].last_seen = None
        # Don't change their status if they're away - let them choose to rejoin
        if table.players[current_pid].status not in ["away", "leaving"]:
            table.players[current_pid].status = "active"
        
        # Send current state to reconnecting player
        await push_state()
        # Broadcast to all players that this player reconnected
        await manager.broadcast_all_states(table)
        save_game_state(tables)
    
    # Continue with message processing (allow temporary PIDs to proceed)

    try:
        while True:
            msg = await ws.receive_json()
            async with table.lock:

                if msg["action"] == "quote":
                    if current_pid != table.maker_pid():
                        await manager.send_personal(current_pid, {"type": "error", "detail": "Only maker can quote"})
                        continue
                    
                    # Check if maker has already quoted in this round
                    has_current_round_quote = any(
                        quote.get("round", -1) == table.round_num 
                        for quote in table.quotes
                    )
                    if has_current_round_quote:
                        await manager.send_personal(current_pid, {"type": "error", "detail": "You have already set a market price for this round"})
                        continue
                    
                    bid = float(msg["bid"])
                    ask = float(msg["ask"])
                    if ask <= bid:
                        await manager.send_personal(current_pid, {"type": "error", "detail": "Ask must be higher than bid"})
                        continue
                    table.quotes.append({"bid": bid, "ask": ask, "round": table.round_num, "maker": current_pid})
                    
                    # Save game state after quote
                    save_game_state(tables)
                    
                    # Broadcast quote event first, then full state
                    await manager.broadcast_table(table, {"type": "quote", "maker": current_pid, "bid": bid, "ask": ask})
                    # Immediately broadcast updated state to all players
                    await manager.broadcast_all_states(table)

                elif msg["action"] == "trade":
                    # Only allow non-makers to trade and only if they haven't traded this round
                    if current_pid == table.maker_pid():
                        await manager.send_personal(current_pid, {"type": "error", "detail": "Market maker cannot trade"})
                        continue
                    
                    if current_pid in table.round_trades:
                        await manager.send_personal(current_pid, {"type": "error", "detail": "You have already traded this round"})
                        continue
                    
                    price = float(msg["price"])
                    side = msg["side"]  # 'buy' or 'sell'
                    table.trades.append({"pid": current_pid, "side": side, "price": price, "round": table.round_num})
                    table.round_trades.append(current_pid)
                    
                    # Save game state after trade
                    save_game_state(tables)
                    
                    await manager.broadcast_table(table, {"type": "trade", "pid": current_pid, "side": side, "price": price})
                    # Also broadcast updated state immediately after trade
                    await manager.broadcast_all_states(table)
                    
                    # Check if all players have traded and auto-advance round
                    if table.all_players_traded_this_round():
                        if table.round_num < 4:
                            table.next_round()
                            if table.round_num == 4:  # settlement
                                table.settle()
                                # Broadcast settlement results first
                                await manager.broadcast_all_states(table)
                                save_game_state(tables)
                                
                                # Notify players of hand completion and delay
                                await manager.broadcast_table(table, {"type": "hand_complete", "message": "Hand complete! Starting new hand..."})
                                
                                # Add delay before starting new hand
                                await asyncio.sleep(2.5)  # 2.5 second delay
                                
                                table.rotate_maker()
                                leaving_players = table.new_hand()
                                
                                # Send events for players who left due to pending status
                                for leaving_player in leaving_players:
                                    # Send leave event to the player who left
                                    await manager.send_personal(leaving_player["pid"], {
                                        "type": "player_event",
                                        "event": "you_left", 
                                        "message": "You have left the table after the hand completed. Your game history is preserved.",
                                        "redirect_to_lobby": True
                                    })
                                    
                                    # Send leave event to all remaining players
                                    await manager.broadcast_table(table, {
                                        "type": "player_event",
                                        "event": "player_left",
                                        "player_id": leaving_player["pid"],
                                        "player_name": leaving_player["name"],
                                        "player_seat": leaving_player["seat"],
                                        "message": f"{leaving_player['name']} has left the table"
                                    })
                        
                        # Save game state after round progression
                        save_game_state(tables)
                        
                        await manager.broadcast_table(table, {"type": "round", "round": table.round_num,
                                                              "community": table.community})
                        # Broadcast complete state after round progression
                        await manager.broadcast_all_states(table)

                # Removed manual next_round - now happens automatically when all players trade

                elif msg["action"] == "leave":
                    # If in the middle of a hand, set pending leaving status
                    if table.round_num > 0 or (table.quotes and len(table.quotes) > 0):
                        table.players[current_pid].status = "pending_leaving"
                        player_name = table.players[current_pid].name
                        
                        await manager.send_personal(current_pid, {
                            "type": "player_event",
                            "event": "you_pending_leave", 
                            "message": "You will leave the table after this hand completes."
                        })
                        
                        # Send event to all players about pending leave
                        await manager.broadcast_table(table, {
                            "type": "player_event",
                            "event": "pending_leave",
                            "player_id": current_pid,
                            "player_name": player_name,
                            "message": f"{player_name} will leave after this hand completes"
                        })
                    else:
                        # Can leave immediately - move to left players and remove from active
                        # Store player info before removal
                        player_name = table.players[current_pid].name
                        player_seat = table.players[current_pid].seat
                        
                        # Move player to left_players and remove from active
                        player = table.players[current_pid]
                        player.status = "left"
                        table.left_players[current_pid] = player
                        del table.players[current_pid]
                        
                        # Remove from seat order
                        if current_pid in table.seat_order:
                            table.seat_order.remove(current_pid)
                        # Adjust maker index if needed
                        if table.seat_order and table.maker_idx >= len(table.seat_order):
                            table.maker_idx = 0
                        
                        # Send leave event to the player who left (keep connection open)
                        await manager.send_personal(current_pid, {
                            "type": "player_event",
                            "event": "you_left", 
                            "message": "You have successfully left the table. Your game history is preserved.",
                            "redirect_to_lobby": True
                        })
                        
                        # Send leave event to all remaining players
                        await manager.broadcast_table(table, {
                            "type": "player_event",
                            "event": "player_left",
                            "player_id": current_pid,
                            "player_name": player_name,
                            "player_seat": player_seat,
                            "message": f"{player_name} has left the table"
                        })
                    
                    save_game_state(tables)
                    await manager.broadcast_all_states(table)

                elif msg["action"] == "join":
                    # Handle joining via WebSocket
                    name = msg.get("name", "").strip()
                    buy_in = msg.get("buy_in", 1000)
                    
                    # Validate input
                    if not name:
                        await manager.send_personal(current_pid, {
                            "type": "join_error",
                            "error": "Name is required"
                        })
                        continue
                    
                    if len(name) > 20:
                        await manager.send_personal(current_pid, {
                            "type": "join_error", 
                            "error": "Name must be 20 characters or less"
                        })
                        continue
                        
                    if buy_in < 1 or buy_in > 10000:
                        await manager.send_personal(current_pid, {
                            "type": "join_error",
                            "error": "Buy-in must be between $1 and $10,000"
                        })
                        continue
                    
                    # Check if name is already taken by an active player
                    name_taken = False
                    for existing_player in table.players.values():
                        if existing_player.name.lower() == name.lower() and existing_player.status != "left":
                            name_taken = True
                            break
                    
                    if name_taken:
                        await manager.send_personal(current_pid, {
                            "type": "join_error",
                            "error": f"Player name '{name}' is already taken. Please choose a different name."
                        })
                        continue
                    
                    # Check if table is full
                    if len([p for p in table.players.values() if p.status != "left"]) >= 7:
                        await manager.send_personal(current_pid, {
                            "type": "join_error",
                            "error": "Table is full"
                        })
                        continue
                    
                    # Find available seat (1-7)
                    occupied_seats = {p.seat for p in table.players.values() if p.status != "left"}
                    available_seats = [i for i in range(1, 8) if i not in occupied_seats]
                    
                    if not available_seats:
                        await manager.send_personal(current_pid, {
                            "type": "join_error",
                            "error": "No available seats"
                        })
                        continue
                    
                    # Assign random available seat
                    seat = random.choice(available_seats)
                    
                    # Generate new player ID (replacing temporary ID)
                    new_pid = str(uuid.uuid4())
                    
                    # Create player with new ID
                    player = Player(pid=new_pid, name=name, seat=seat, stack=buy_in, buy_in=buy_in)
                    table.players[new_pid] = player
                    
                    # Update seat order for maker rotation
                    if new_pid not in table.seat_order:
                        table.seat_order.append(new_pid)
                    
                    # Update connection manager to use new PID
                    manager.update_player_id(current_pid, new_pid)
                    # Update current PID for this WebSocket session
                    current_pid = new_pid
                    
                    # Send successful join response
                    await manager.send_personal(new_pid, {
                        "type": "join_success",
                        "pid": new_pid,
                        "tid": tid,
                        "player": player.to_public(reveal_cards=True),
                        "message": f"Welcome to the table, {name}!"
                    })
                    
                    # Send player joined event to all other players
                    await manager.broadcast_table(table, {
                        "type": "player_event",
                        "event": "player_joined",
                        "player_id": new_pid,
                        "player_name": name,
                        "player_seat": seat,
                        "message": f"{name} joined the table"
                    })
                    
                    # Auto-start a new hand if we have 2+ players and no hand is in progress
                    active_players = [p for p in table.players.values() if p.status == "active"]
                    if len(active_players) >= 2 and table.round_num == 0 and not table.community:
                        leaving_players = table.new_hand()
                        print(f"Auto-started new hand with {len(active_players)} players")
                    
                    save_game_state(tables)
                    await manager.broadcast_all_states(table)

                elif msg["action"] == "away":
                    # If in the middle of a hand, set pending away status
                    if table.round_num > 0 or (table.quotes and len(table.quotes) > 0):
                        table.players[current_pid].status = "pending_away"
                        await manager.send_personal(current_pid, {
                            "type": "info", 
                            "detail": "You will be marked as away after this hand completes."
                        })
                    else:
                        # Can go away immediately
                        table.players[current_pid].status = "away"
                    
                    save_game_state(tables)
                    await manager.broadcast_all_states(table)

                elif msg["action"] == "join_back":
                    # Player wants to rejoin from away or cancel pending statuses
                    if current_pid in table.players:
                        player_status = table.players[current_pid].status
                        
                        if player_status in ["pending_away", "pending_leaving"]:
                            # Cancel pending status
                            table.players[current_pid].status = "active"
                            save_game_state(tables)
                            await manager.broadcast_all_states(table)
                        elif player_status == "away":
                            # Only allow rejoining between hands (round 0 means new hand starting)
                            if table.round_num == 0:
                                table.players[current_pid].status = "active"
                                save_game_state(tables)
                                await manager.broadcast_all_states(table)
                            else:
                                await manager.send_personal(current_pid, {
                                    "type": "error", 
                                    "detail": "Cannot rejoin in the middle of a hand. Please wait for the next hand."
                                })

                elif msg["action"] == "ping":
                    # Heartbeat - respond with pong
                    await manager.send_personal(current_pid, {"type": "pong"})

            await push_state()

    except WebSocketDisconnect:
        manager.disconnect(current_pid)
        # Don't remove player from table on disconnect - they might reconnect
        # Just mark them as temporarily disconnected
        if current_pid in table.players:
            table.players[current_pid].last_seen = asyncio.get_event_loop().time()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)