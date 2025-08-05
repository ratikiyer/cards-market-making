<script lang="ts">
  import Card from './Card.svelte';

  export let player: any;
  export let isCurrentPlayer: boolean;
  export let isMaker: boolean;

  function formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }

  function getStatusColor(pnl: number): string {
    if (pnl > 0) return '#4CAF50';
    if (pnl < 0) return '#F44336';
    return '#FFC107';
  }
</script>

<div class="player-seat" class:current-player={isCurrentPlayer} class:away={player.status === 'away'} class:pending-away={player.status === 'pending_away'} class:pending-leaving={player.status === 'pending_leaving'}>
  <div class="player-info">
    <div class="player-name">
      {player.name}
      {#if isMaker}
        <div class="maker-button">M</div>
      {/if}
    </div>
    
    <div class="player-stats">
      <div class="stack">
        Stack: {formatCurrency(player.stack)}
      </div>
      <div class="pnl" style="color: {getStatusColor(player.pnl)}">
        P&L: {player.pnl >= 0 ? '+' : ''}{formatCurrency(player.pnl)}
      </div>
    </div>

    <!-- Always show cards for all players, but hide others' cards -->
    <div class="hole-cards">
      {#if player.cards && player.cards.length > 0}
        {#each player.cards as card}
          <Card {card} hidden={!isCurrentPlayer} size="medium" />
        {/each}
      {:else}
        <!-- Show placeholder cards when no cards are dealt yet -->
        <Card card="" hidden={true} size="medium" />
        <Card card="" hidden={true} size="medium" />
      {/if}
    </div>

    {#if player.status === 'away'}
      <div class="status-indicator away">AWAY</div>
    {:else if player.status === 'pending_away'}
      <div class="status-indicator pending-away">AWAY NEXT HAND</div>
    {:else if player.status === 'pending_leaving'}
      <div class="status-indicator pending-leaving">LEAVING NEXT HAND</div>
    {:else if player.status === 'leaving'}
      <div class="status-indicator leaving">LEAVING</div>
    {/if}
  </div>
</div>

<style>
  .player-seat {
    width: 100%;
    height: 100%;
    background: linear-gradient(145deg, #2d2d44, #252538);
    border: 2px solid #444;
    border-radius: 12px;
    padding: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
    position: relative;
    min-height: 100px;
  }

  .player-seat.current-player {
    border-color: #4CAF50;
    box-shadow: 0 0 15px rgba(76, 175, 80, 0.3);
  }

  .player-seat.away {
    opacity: 0.6;
    filter: grayscale(50%);
  }

  .player-info {
    display: flex;
    flex-direction: column;
    height: 100%;
    text-align: center;
  }

  .player-name {
    font-weight: bold;
    font-size: 0.9rem;
    color: #fff;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }

  .maker-button {
    background: #dc3545;
    color: white;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: bold;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  .player-stats {
    font-size: 0.7rem;
    margin-bottom: 6px;
  }

  .stack {
    color: #ccc;
    margin-bottom: 2px;
  }

  .pnl {
    font-weight: bold;
  }

  .hole-cards {
    display: flex;
    justify-content: center;
    gap: 3px;
    margin-top: auto;
  }

  .status-indicator {
    position: absolute;
    top: -8px;
    right: -8px;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 0.6rem;
    font-weight: bold;
    text-transform: uppercase;
  }

  .status-indicator.away {
    background: #FFC107;
    color: #000;
  }

  .status-indicator.pending-away {
    background: #FF9800;
    color: white;
    font-size: 0.5rem;
    padding: 1px 4px;
  }

  .status-indicator.pending-leaving {
    background: #E91E63;
    color: white;
    font-size: 0.45rem;
    padding: 1px 3px;
  }

  .status-indicator.leaving {
    background: #F44336;
    color: white;
  }

  .player-seat.pending-away {
    opacity: 0.8;
    border: 2px dashed #FF9800;
  }

  .player-seat.pending-leaving {
    opacity: 0.8;
    border: 2px dashed #E91E63;
  }
</style> 