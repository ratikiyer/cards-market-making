<script lang="ts">
  export let trades: any[];
  export let quotes: any[];
  export let players: any[];

  function getPlayerName(pid: string): string {
    const player = players.find(p => p.pid === pid);
    return player ? player.name : 'Unknown';
  }

  function formatTime(timestamp?: number): string {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleTimeString();
  }

  // Combine and sort trades and quotes by timestamp/order - most recent first
  $: logEntries = [
    ...trades.map((trade, index) => ({
      ...trade,
      type: 'trade',
      timestamp: Date.now() - (trades.length - index) * 1000, // Simulate timestamps
      order: trades.length - index
    })),
    ...quotes.map((quote, index) => ({
      ...quote,
      type: 'quote',
      timestamp: Date.now() - (quotes.length - index) * 1000 - 500, // Quotes come before trades
      order: quotes.length - index
    }))
  ].sort((a, b) => b.timestamp - a.timestamp); // Most recent first
</script>

<div class="game-log">
  <div class="log-header">
    <h3>📊 Game Log</h3>
    <div class="log-count">{logEntries.length} entries</div>
  </div>

  <div class="log-content">
    {#if logEntries.length === 0}
      <div class="empty-log">
        No activity yet
      </div>
    {:else}
      {#each logEntries as entry}
        <div class="log-entry {entry.type}">
          {#if entry.type === 'trade'}
            <div class="trade-entry">
              <div class="entry-header">
                <div class="trade-header">
                  <span class="player-name">{getPlayerName(entry.pid)}</span>
                  <span class="trade-action {entry.side}">{entry.side.toUpperCase()}</span>
                  <span class="trade-price">@ {entry.price}</span>
                </div>
                <div class="entry-time">Round {entry.round + 1}</div>
              </div>
            </div>
          {:else if entry.type === 'quote'}
            <div class="quote-entry">
              <div class="entry-header">
                <div class="quote-header">
                  <span class="market-label">📈 {getPlayerName(entry.maker)} Published Market</span>
                  <div class="quote-prices">
                    <span class="bid">Bid: {entry.bid}</span>
                    <span class="ask">Ask: {entry.ask}</span>
                    <span class="spread">Spread: {entry.ask - entry.bid}</span>
                  </div>
                </div>
                <div class="entry-time">Round {entry.round + 1}</div>
              </div>
            </div>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .game-log {
    height: 100%;
    background: #2d2d44;
    border-radius: 12px;
    border: 1px solid #444;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .log-header {
    padding: 16px 20px 12px 20px;
    border-bottom: 1px solid #444;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .log-header h3 {
    margin: 0;
    color: #4CAF50;
    font-size: 1.1rem;
  }

  .log-count {
    color: #888;
    font-size: 0.8rem;
  }

  .log-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  .empty-log {
    text-align: center;
    color: #666;
    font-style: italic;
    padding: 40px 20px;
  }

  .log-entry {
    margin-bottom: 8px;
    padding: 12px;
    border-radius: 8px;
    background: #1a1a2e;
    border-left: 3px solid transparent;
  }

  .log-entry.trade {
    border-left-color: #4CAF50;
  }

  .log-entry.quote {
    border-left-color: #2196F3;
  }

  .entry-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 4px;
  }

  .trade-header {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
  }

  .player-name {
    font-weight: bold;
    color: #fff;
    font-size: 0.9rem;
  }

  .trade-action {
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: bold;
  }

  .trade-action.buy {
    background: #4CAF50;
    color: white;
  }

  .trade-action.sell {
    background: #F44336;
    color: white;
  }

  .trade-price {
    color: #FFC107;
    font-weight: bold;
    font-size: 0.9rem;
  }

  .quote-header {
    flex: 1;
  }

  .market-label {
    color: #2196F3;
    font-weight: bold;
    font-size: 0.9rem;
    display: block;
    margin-bottom: 4px;
  }

  .quote-prices {
    display: flex;
    gap: 12px;
    font-size: 0.8rem;
  }

  .quote-prices .bid {
    color: #F44336;
  }

  .quote-prices .ask {
    color: #4CAF50;
  }

  .quote-prices .spread {
    color: #FFC107;
    font-size: 0.8rem;
  }

  .entry-time {
    color: #888;
    font-size: 0.7rem;
    white-space: nowrap;
    margin-left: 8px;
  }

  /* Custom scrollbar */
  .log-content::-webkit-scrollbar {
    width: 6px;
  }

  .log-content::-webkit-scrollbar-track {
    background: #1a1a2e;
    border-radius: 3px;
  }

  .log-content::-webkit-scrollbar-thumb {
    background: #555;
    border-radius: 3px;
  }

  .log-content::-webkit-scrollbar-thumb:hover {
    background: #666;
  }
</style> 