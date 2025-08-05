<script lang="ts">
  export let sortedPlayers: any[];
  export let onClose: () => void;

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }

  function getPositionEmoji(index: number): string {
    switch (index) {
      case 0: return '🥇';
      case 1: return '🥈';
      case 2: return '🥉';
      default: return `${index + 1}.`;
    }
  }

  function getStatusColor(pnl: number): string {
    if (pnl > 0) return '#4CAF50';
    if (pnl < 0) return '#F44336';
    return '#FFC107';
  }
</script>

<div class="modal-overlay" on:click={onClose} on:keydown={(e) => e.key === 'Escape' && onClose()} role="button" tabindex="0">
  <div class="leaderboard-modal" on:click|stopPropagation role="dialog">
    <div class="modal-header">
      <h2>🏆 Leaderboard</h2>
      <button class="close-btn" on:click={onClose}>✕</button>
    </div>

    <div class="leaderboard-content">
      {#if sortedPlayers.length === 0}
        <div class="empty-state">
          No players yet. Waiting for players to join...
        </div>
      {:else}
        <div class="leaderboard-list">
          {#each sortedPlayers as player, index}
            <div class="player-row" class:top-performer={index < 3}>
              <div class="position">
                {getPositionEmoji(index)}
              </div>
              
              <div class="player-info">
                <div class="player-name">
                  {player.name}
                  {#if player.status === 'away'}
                    <span class="status away">AWAY</span>
                  {:else if player.status === 'pending_away'}
                    <span class="status pending-away">AWAY NEXT</span>
                  {:else if player.status === 'pending_leaving'}
                    <span class="status pending-leaving">LEAVING NEXT</span>
                  {:else if player.status === 'leaving'}
                    <span class="status leaving">LEAVING</span>
                  {:else if player.status === 'left' || player.has_left}
                    <span class="status left">LEFT</span>
                  {/if}
                </div>
                <div class="player-seat">Seat {player.seat}</div>
              </div>

              <div class="player-stats">
                <div class="current-stack">
                  <span class="stat-label">Stack:</span>
                  <span>{formatCurrency(player.stack)}</span>
                </div>
                <div class="pnl" style="color: {getStatusColor(player.pnl)}">
                  <span class="stat-label">P&L:</span>
                  <span class="pnl-amount">
                    {player.pnl >= 0 ? '+' : ''}{formatCurrency(player.pnl)}
                  </span>
                </div>
              </div>

              <div class="performance-indicator">
                {#if player.pnl > 0}
                  <div class="indicator positive">↗️</div>
                {:else if player.pnl < 0}
                  <div class="indicator negative">↘️</div>
                {:else}
                  <div class="indicator neutral">➡️</div>
                {/if}
              </div>
            </div>
          {/each}
        </div>

        <div class="leaderboard-summary">
          <div class="total-players">
            <strong>Total Players:</strong> {sortedPlayers.length}
          </div>
          <div class="total-money">
            <strong>Total Money in Play:</strong> 
            {formatCurrency(sortedPlayers.reduce((sum, p) => sum + p.stack, 0))}
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .leaderboard-modal {
    background: #2d2d44;
    border-radius: 16px;
    border: 1px solid #444;
    width: 90%;
    max-width: 600px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 24px 24px 16px 24px;
    border-bottom: 1px solid #444;
  }

  .modal-header h2 {
    margin: 0;
    color: #4CAF50;
    font-size: 1.5rem;
  }

  .close-btn {
    background: none;
    border: none;
    color: #888;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: color 0.2s ease;
  }

  .close-btn:hover {
    color: #fff;
    background: #444;
  }

  .leaderboard-content {
    flex: 1;
    overflow-y: auto;
    padding: 16px 24px 24px 24px;
  }

  .empty-state {
    text-align: center;
    color: #666;
    font-style: italic;
    padding: 60px 20px;
  }

  .leaderboard-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 24px;
  }

  .player-row {
    display: flex;
    align-items: center;
    padding: 16px;
    background: #1a1a2e;
    border-radius: 12px;
    border: 1px solid #333;
    transition: all 0.2s ease;
  }

  .player-row:hover {
    border-color: #555;
    transform: translateY(-1px);
  }

  .player-row.top-performer {
    background: linear-gradient(135deg, #1a1a2e, #2d2d44);
    border-color: #4CAF50;
  }

  .position {
    font-size: 1.5rem;
    margin-right: 16px;
    min-width: 40px;
    text-align: center;
  }

  .player-info {
    flex: 1;
    margin-right: 16px;
  }

  .player-name {
    font-weight: bold;
    color: #fff;
    font-size: 1.1rem;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .player-seat {
    color: #888;
    font-size: 0.9rem;
  }

  .status {
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: bold;
  }

  .status.away {
    background: #FFC107;
    color: #000;
  }

  .status.pending-away {
    background: #FF9800;
    color: white;
  }

  .status.pending-leaving {
    background: #E91E63;
    color: white;
  }

  .status.leaving {
    background: #F44336;
    color: white;
  }

  .status.left {
    background: #9E9E9E;
    color: white;
  }

  .player-stats {
    text-align: right;
    margin-right: 16px;
  }

  .current-stack, .pnl {
    margin-bottom: 4px;
    font-size: 0.9rem;
  }

  .player-stats .stat-label {
    color: #888;
    margin-right: 6px;
  }

  .pnl-amount {
    font-weight: bold;
  }

  .performance-indicator {
    font-size: 1.2rem;
  }

  .indicator {
    padding: 4px;
    border-radius: 4px;
  }

  .leaderboard-summary {
    background: #1a1a2e;
    border-radius: 8px;
    padding: 16px;
    border: 1px solid #333;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }

  .leaderboard-summary > div {
    color: #ccc;
    font-size: 0.9rem;
  }

  /* Custom scrollbar */
  .leaderboard-content::-webkit-scrollbar {
    width: 6px;
  }

  .leaderboard-content::-webkit-scrollbar-track {
    background: #1a1a2e;
    border-radius: 3px;
  }

  .leaderboard-content::-webkit-scrollbar-thumb {
    background: #555;
    border-radius: 3px;
  }

  .leaderboard-content::-webkit-scrollbar-thumb:hover {
    background: #666;
  }
</style> 