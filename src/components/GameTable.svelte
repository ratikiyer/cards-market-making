<script lang="ts">
  import type { Writable } from 'svelte/store';
  import PlayerSeat from './PlayerSeat.svelte';
  import CommunityCards from './CommunityCards.svelte';
  import ActionPanel from './ActionPanel.svelte';
  import GameLog from './GameLog.svelte';
  import Leaderboard from './Leaderboard.svelte';
  import MarketMakerPanel from './MarketMakerPanel.svelte';
  import Options from './Options.svelte';
  import WidthAuction from './WidthAuction.svelte';

  export let gameState: Writable<any>;
  export let pid: Writable<string>;
  export let connectionStatus: Writable<string>;
  export let sendMessage: (action: any) => void;

  $: currentPlayer = $gameState.players?.find((p: any) => p.pid === $pid);
  $: isMaker = $gameState.maker === $pid;
  $: canMakeMarket = isMaker && (!auctionEnabled || auctionCompletedThisRound);
  $: sortedPlayers = $gameState.all_players ? 
    [...$gameState.all_players].sort((a: any, b: any) => b.pnl - a.pnl) : 
    ($gameState.players ? [...$gameState.players].sort((a: any, b: any) => b.pnl - a.pnl) : []);

  let showOptions = false;
  let showLeaderboard = false;
  let showLog = true;
  let showMarketMakerPanel = false;
  let hasSubmittedQuoteThisRound = false;
  let auctionStartAttempted = false; // Track if we've attempted to start auction this round
  
  // Auction state
  $: auctionEnabled = $gameState.auction_enabled || false;
  $: widthAuctionActive = $gameState.width_auction_active || false;
  $: auctionCompletedThisRound = $gameState.auction_completed_this_round || false;
  $: currentMaxWidth = $gameState.current_max_width || 10;
  $: awaitingHandStart = $gameState.awaiting_hand_start || false;

  // Auto-trigger auction when conditions are met
  $: {
    if (auctionEnabled && 
        !widthAuctionActive && 
        !auctionCompletedThisRound && 
        $gameState.players && 
        $gameState.players.length >= 2 &&
        !hasCurrentRoundQuote &&
        !auctionStartAttempted &&
        !awaitingHandStart &&
        $gameState.round !== undefined &&
        $gameState.round >= 0 && 
        $gameState.round <= 3) {
      // Small delay to ensure all state updates are processed
      setTimeout(() => {
        if (auctionEnabled && 
            !$gameState.width_auction_active && 
            !$gameState.auction_completed_this_round &&
            !auctionStartAttempted &&
            !$gameState.awaiting_hand_start &&
            $gameState.round !== undefined &&
            $gameState.round >= 0 && 
            $gameState.round <= 3) {
          auctionStartAttempted = true;
          sendMessage({ action: 'start_width_auction' });
        }
      }, 100);
    }
  }

  // Computed values for game state
  $: hasCurrentRoundQuote = $gameState.quotes?.some((quote: any) => quote.round === $gameState.round) || false;
  $: needsMarketMaker = canMakeMarket && $gameState.players && $gameState.players.length >= 2 && !hasCurrentRoundQuote;

  // Reset quote submission flag when round changes
  let previousRound = -1;
  $: {
    if ($gameState.round !== undefined && $gameState.round !== previousRound) {
      hasSubmittedQuoteThisRound = false;
      auctionStartAttempted = false; // Reset auction attempt flag for new round
      previousRound = $gameState.round;
    }
  }

  // Don't auto-open market maker panel - let user click the button

  function handleTrade(side: 'buy' | 'sell') {
    const currentQuote = $gameState.quotes?.[$gameState.quotes?.length - 1];
    if (!currentQuote) {
      alert('No current market quote available');
      return;
    }
    
    // Use the quoted price: buy at ask, sell at bid
    const price = side === 'buy' ? currentQuote.ask : currentQuote.bid;
    sendMessage({ action: 'trade', side, price });
  }

  function handleQuote(bid: number, ask: number) {
    console.log('GameTable handleQuote called', { bid, ask });
    sendMessage({ action: 'quote', bid, ask });
    showMarketMakerPanel = false;
    hasSubmittedQuoteThisRound = true; // Prevent auto-reopening this round
  }

  function closeMarketMakerPanel() {
    showMarketMakerPanel = false;
  }

  function toggleAwayStatus() {
    if (currentPlayer?.status === 'away') {
      // Rejoin the game
      sendMessage({ action: 'join_back' });
    } else if (currentPlayer?.status === 'pending_away') {
      // Cancel pending away status by setting back to active
      sendMessage({ action: 'join_back' }); // This will set status back to active
    } else {
      // Go away (will be immediate or pending based on game state)
      sendMessage({ action: 'away' });
    }
  }

  function toggleLeaveStatus() {
    if (currentPlayer?.status === 'pending_leaving') {
      // Cancel pending leave status
      sendMessage({ action: 'join_back' });
    } else {
      // Leave the table (will be immediate or pending based on game state)
      sendMessage({ action: 'leave' });
    }
  }

  function startHand() {
    sendMessage({ action: 'start_hand' });
  }

  // Removed nextRound function - now automatic

  // Create an array of 7 seats with players positioned correctly
  $: seats = Array(7).fill(null).map((_, index) => {
    const seatNumber = index + 1;
    return $gameState.players?.find((p: any) => p.seat === seatNumber) || null;
  });
</script>

<div class="game-container">
  <!-- Top Bar -->
  <div class="top-bar">
    <div class="top-left">
      <button class="btn btn-secondary options-btn" on:click={() => showOptions = !showOptions}>
        ⚙️ Options
      </button>
      <button class="btn {currentPlayer?.status === 'pending_leaving' ? 'btn-warning' : 'btn-danger'} leave-btn" on:click={toggleLeaveStatus}>
        {currentPlayer?.status === 'pending_leaving' ? '↩️ Cancel Leave' : '🚪 Leave Seat'}
      </button>
      <button class="btn {currentPlayer?.status === 'away' ? 'btn-primary' : (currentPlayer?.status === 'pending_away' ? 'btn-warning' : 'btn-secondary')} away-btn" on:click={toggleAwayStatus}>
        {currentPlayer?.status === 'away' ? '🎮 Join' : (currentPlayer?.status === 'pending_away' ? '⏳ Away Next Hand' : '⏸️ Away')}
      </button>
      <button class="btn btn-secondary log-toggle" on:click={() => showLog = !showLog}>
        {showLog ? '📊 Hide Log' : '📊 Show Log'}
      </button>
      {#if awaitingHandStart}
        <button class="btn btn-primary start-hand-btn" on:click={startHand}>
          🎯 Start Hand
        </button>
      {/if}
    </div>
    
    <div class="top-center">
      <h1>Cards Market Making Game</h1>
      <div class="round-info">
        Round {$gameState.round + 1} of 4
        {#if isMaker}
          <span class="maker-indicator">• You are the Market Maker</span>
        {/if}
      </div>
    </div>
    
    <div class="top-right">
      <div class="connection-status {$connectionStatus}">
        {$connectionStatus === 'connected' ? '🟢' : 
         $connectionStatus === 'connecting' ? '🟡' : '🔴'} 
        {$connectionStatus}
      </div>
      <button class="btn btn-secondary leaderboard-btn" on:click={() => showLeaderboard = !showLeaderboard}>
        🏆 Leaderboard
      </button>
    </div>
  </div>

  <!-- Main Content -->
  <div class="main-content">
    <!-- Side Log -->
    {#if showLog}
      <div class="side-log">
        <GameLog 
          trades={$gameState.trades || []} 
          quotes={$gameState.quotes || []} 
          players={$gameState.players || []}
        />
      </div>
    {/if}

    <!-- Game Area -->
    <div class="game-area" class:full-width={!showLog}>
      <!-- Trading Actions Area - Top of table -->
      <div class="trading-area">
        <!-- Action Panel - For non-makers who haven't traded yet and are active -->
        {#if !isMaker && currentPlayer && (currentPlayer.status === 'active' || currentPlayer.status === 'pending_away' || currentPlayer.status === 'pending_leaving') && hasCurrentRoundQuote}
          <ActionPanel 
            {handleTrade}
            currentQuote={$gameState.quotes?.[$gameState.quotes?.length - 1]}
          />
        {:else if isMaker && !hasCurrentRoundQuote && $gameState.round !== undefined && $gameState.round >= 0 && $gameState.round <= 3}
          <div class="maker-actions">
            {#if auctionEnabled && !auctionCompletedThisRound}
              <!-- Show status when auction is enabled but not completed -->
              {#if widthAuctionActive}
                <div class="auction-in-progress">
                  <span class="auction-status">🔨 Auction in Progress...</span>
                </div>
              {:else}
                <div class="auction-pending">
                  <span class="auction-status">⏳ Starting Auction...</span>
                </div>
              {/if}
            {:else if auctionEnabled && auctionCompletedThisRound}
              <!-- Show completed status when auction is done - only auction winner can quote -->
              {#if canMakeMarket}
                <div class="auction-complete">
                  <span class="auction-status">✅ Auction Complete</span>
                  <button class="btn btn-danger set-market-btn" on:click={() => showMarketMakerPanel = true}>
                    Quote Market
                  </button>
                </div>
              {:else}
                <div class="auction-complete">
                  <span class="auction-status">✅ Auction Won by Another Player</span>
                </div>
              {/if}
            {:else}
              <!-- Normal mode - show quote market button directly -->
              <button class="btn btn-danger set-market-btn" on:click={() => showMarketMakerPanel = true}>
                Quote Market
              </button>
            {/if}
          </div>
        {:else if $gameState.players && $gameState.players.length < 2}
          <div class="waiting-message">Waiting for more players to join...</div>
        {:else if !hasCurrentRoundQuote}
          <div class="waiting-message">Waiting for market maker's quote...</div>
        {:else if currentPlayer?.status === 'away'}
          <div class="away-message">You are away...</div>
        {:else}
          <div class="status-message">Waiting for all players to trade...</div>
        {/if}
      </div>

      <!-- Table -->
      <div class="poker-table">
        <!-- Community Cards -->
        <div class="table-center">
          <CommunityCards cards={$gameState.community || []} round={$gameState.round} />
        </div>

        <!-- Player Seats -->
        {#each seats as player, index}
          <div class="seat seat-{index + 1}" class:occupied={player}>
            {#if player}
              <PlayerSeat 
                {player} 
                isCurrentPlayer={player.pid === $pid}
                isMaker={player.pid === $gameState.maker}
              />
            {:else}
              <div class="empty-seat">
                <div class="seat-number">Seat {index + 1}</div>
                <div class="empty-text">Empty</div>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- Market Maker Panel - Only shows automatically for makers -->
  {#if canMakeMarket && showMarketMakerPanel}
    <MarketMakerPanel 
      onQuote={handleQuote}
      currentQuote={$gameState.quotes?.[$gameState.quotes?.length - 1]}
      currentMaxWidth={currentMaxWidth}
      onClose={closeMarketMakerPanel}
      gameState={$gameState}
    />
  {/if}

  <!-- Modals -->
  {#if showLeaderboard}
    <Leaderboard {sortedPlayers} onClose={() => showLeaderboard = false} />
  {/if}

  {#if showOptions}
    <Options 
      gameState={$gameState}
      sendMessage={sendMessage}
      onClose={() => showOptions = false}
    />
  {/if}

  <!-- Width Auction Modal -->
  {#if widthAuctionActive}
    <WidthAuction 
      gameState={$gameState}
      pid={$pid}
      sendMessage={sendMessage}
    />
  {/if}
</div>

<style>
  .game-container {
    width: 100vw;
    height: 100vh;
    background: linear-gradient(135deg, #0f3460 0%, #16537e 100%);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: rgba(0, 0, 0, 0.3);
    border-bottom: 1px solid #444;
  }

  .top-left, .top-right {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .top-center {
    text-align: center;
  }

  .top-center h1 {
    margin: 0;
    font-size: 1.5rem;
    color: #4CAF50;
  }

  .round-info {
    color: #ccc;
    font-size: 0.9rem;
    margin-top: 4px;
  }

  .maker-indicator {
    color: #dc3545;
    font-weight: bold;
  }

  .connection-status {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
  }

  .connection-status.connected {
    background: rgba(76, 175, 80, 0.2);
    color: #4CAF50;
  }

  .connection-status.connecting {
    background: rgba(255, 193, 7, 0.2);
    color: #FFC107;
  }

  .connection-status.disconnected,
  .connection-status.error {
    background: rgba(244, 67, 54, 0.2);
    color: #F44336;
  }

  .main-content {
    flex: 1;
    display: flex;
    overflow: hidden;
  }

  .side-log {
    width: 320px;
    height: 100%;
    padding: 20px;
    background: rgba(0, 0, 0, 0.2);
    border-right: 1px solid #444;
  }

  .game-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 20px;
    position: relative;
    gap: 20px;
  }

  .game-area.full-width {
    margin-left: 0;
  }

  .trading-area {
    position: absolute;
    top: 200px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 80px;
    width: 100%;
    z-index: 10;
  }

  .maker-actions {
    display: flex;
    justify-content: center;
  }

  .set-market-btn {
    padding: 12px 24px;
    font-size: 16px;
    font-weight: 600;
  }

  .waiting-message, .away-message, .status-message {
    text-align: center;
    padding: 12px 24px;
    background: rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    color: #ccc;
    font-size: 14px;
  }

  .poker-table {
    position: relative;
    width: 1000px;
    height: 600px;
    border: 8px solid #8B4513;
    background: #0a4d3a;
    border-radius: 300px;
    box-shadow: 
      inset 0 0 60px rgba(0, 0, 0, 0.3),
      0 0 60px rgba(0, 0, 0, 0.5);
  }

  .table-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
  }

  .game-status {
    margin-top: 20px;
  }

  .status-message {
    background: rgba(0, 0, 0, 0.4);
    color: #ccc;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 0.9rem;
  }

  .status-action-btn {
    padding: 12px 24px;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 8px;
    margin: 8px 0;
  }

  .away-message {
    color: #FFC107;
    border: 1px solid #FFC107;
    margin-bottom: 12px;
  }

  .waiting-message {
    color: #FFC107;
    background: rgba(255, 193, 7, 0.1);
    padding: 12px 20px;
    border-radius: 8px;
    font-weight: 500;
  }

  .seat {
    position: absolute;
    width: 140px;
    height: 100px;
    transform: translate(-50%, -50%);
  }

  /* Seat positions around the oval table - adjusted for larger table */
  .seat-1 { top: 25%; left: 5%; }   /* Left side */
  .seat-2 { top: 60%; left: 5%; }   /* Left side lower */
  .seat-3 { top: 90%; left: 22%; }  /* Bottom left */
  .seat-4 { top: 90%; left: 50%; }  /* Bottom center */
  .seat-5 { top: 90%; left: 78%; }  /* Bottom right */
  .seat-6 { top: 60%; left: 95%; }  /* Right side lower */
  .seat-7 { top: 25%; left: 95%; }  /* Right side */

  .empty-seat {
    width: 100%;
    height: 100%;
    border: 2px dashed #669;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: rgba(255, 255, 255, 0.05);
  }

  .seat-number {
    font-weight: bold;
    color: #888;
    font-size: 0.9rem;
  }

  .empty-text {
    color: #666;
    font-size: 0.8rem;
    margin-top: 4px;
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .modal {
    background: #2d2d44;
    border-radius: 12px;
    padding: 30px;
    border: 1px solid #444;
    text-align: center;
  }

  .modal h3 {
    margin-top: 0;
    color: #4CAF50;
  }

  .auction-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .auction-btn:disabled:hover {
    transform: none;
    box-shadow: none;
  }

  .auction-in-progress, .auction-complete {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .auction-pending {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 8px;
    background: rgba(255, 193, 7, 0.1);
    border-radius: 8px;
    border: 1px solid rgba(255, 193, 7, 0.3);
  }

  .auction-status {
    color: #ff8c42;
    font-weight: 600;
    font-size: 1rem;
  }

  .auction-complete {
    padding: 8px;
    background: rgba(76, 175, 80, 0.1);
    border-radius: 8px;
    border: 1px solid rgba(76, 175, 80, 0.3);
  }

  .auction-in-progress {
    padding: 8px;
    background: rgba(255, 140, 66, 0.1);
    border-radius: 8px;
    border: 1px solid rgba(255, 140, 66, 0.3);
  }
</style> 