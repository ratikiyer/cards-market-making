<script lang="ts">
  export let handleTrade: (side: 'buy' | 'sell') => void;
  export let currentQuote: any;
</script>

<div class="action-panel">
  <h3>Market</h3>
  
  {#if currentQuote}
    <div class="current-market">
      <div class="market-header">Current Market</div>
      <div class="market-display">
        <div class="bid">
          <span class="label">Bid</span>
          <span class="price">{currentQuote.bid}</span>
        </div>
        <div class="spread">
          <span class="spread-value">
            Spread: {currentQuote.ask - currentQuote.bid}
          </span>
        </div>
        <div class="ask">
          <span class="label">Ask</span>
          <span class="price">{currentQuote.ask}</span>
        </div>
      </div>
    </div>
  {:else}
    <div class="no-market">
      Waiting for maker to quote market...
    </div>
  {/if}

  <div class="trade-buttons">
    <button 
      class="btn trade-btn sell-btn" 
      on:click={() => handleTrade('sell')}
      disabled={!currentQuote}
    >
      SELL
      {#if currentQuote}
        <div class="btn-price">@ {currentQuote.bid}</div>
      {/if}
    </button>
    
    <button 
      class="btn trade-btn buy-btn" 
      on:click={() => handleTrade('buy')}
      disabled={!currentQuote}
    >
      BUY
      {#if currentQuote}
        <div class="btn-price">@ {currentQuote.ask}</div>
      {/if}
    </button>
  </div>
</div>

<style>
  .action-panel {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: #2d2d44;
    border: 2px solid #4CAF50;
    border-radius: 12px;
    padding: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    min-width: 380px;
    text-align: center;
  }

  .action-panel h3 {
    margin: 0 0 16px 0;
    color: #4CAF50;
    font-size: 1.1rem;
  }

  .current-market {
    margin-bottom: 20px;
    background: #1a1a2e;
    border-radius: 8px;
    padding: 12px;
  }

  .market-header {
    color: #ccc;
    font-size: 0.9rem;
    margin-bottom: 8px;
    font-weight: 500;
  }

  .market-display {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .bid, .ask {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .bid .label {
    color: #F44336;
    font-size: 0.8rem;
    font-weight: bold;
  }

  .ask .label {
    color: #4CAF50;
    font-size: 0.8rem;
    font-weight: bold;
  }

  .bid .price, .ask .price {
    font-size: 1.2rem;
    font-weight: bold;
    color: white;
    margin-top: 2px;
  }

  .spread {
    text-align: center;
  }

  .spread-value {
    color: #FFC107;
    font-size: 0.8rem;
    font-weight: 500;
  }

  .no-market {
    color: #888;
    font-style: italic;
    padding: 20px;
    background: #1a1a2e;
    border-radius: 8px;
    margin-bottom: 20px;
  }

  .trade-buttons {
    display: flex;
    gap: 12px;
    margin-bottom: 0;
  }

  .trade-btn {
    flex: 1;
    padding: 16px;
    font-size: 1rem;
    font-weight: bold;
    border-radius: 8px;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: all 0.2s ease;
  }

  .buy-btn {
    background: #4CAF50;
    color: white;
  }

  .buy-btn:hover:not(:disabled) {
    background: #45a049;
    transform: translateY(-2px);
  }

  .sell-btn {
    background: #F44336;
    color: white;
  }

  .sell-btn:hover:not(:disabled) {
    background: #da190b;
    transform: translateY(-2px);
  }

  .trade-btn:disabled {
    background: #666;
    cursor: not-allowed;
    transform: none;
  }

  .btn-price {
    font-size: 1rem;
    font-weight: bold;
    opacity: 0.9;
  }
</style> 