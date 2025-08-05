<script lang="ts">
  export let onQuote: (bid: number, ask: number) => void;
  export let currentQuote: any;
  export let onClose: () => void = () => {};

  let bidPrice = currentQuote?.bid || 50;
  let askPrice = currentQuote?.ask || 55;

  // Initialize default values when component loads
  if (currentQuote) {
    bidPrice = currentQuote.bid;
    askPrice = currentQuote.ask;
  }

  function handleQuote() {
    if (askPrice <= bidPrice) {
      alert('Ask must be higher than bid');
      return;
    }
    if (bidPrice <= 0 || askPrice <= 0) {
      alert('Prices must be positive');
      return;
    }
    onQuote(bidPrice, askPrice);
    onClose(); // Close the panel after submitting
  }

  function handleClose() {
    onClose();
  }

  $: spread = askPrice - bidPrice;
</script>

<!-- Show modal directly when component is rendered -->
<div class="modal-overlay" on:click={handleClose} on:keydown={(e) => e.key === 'Escape' && handleClose()} role="button" tabindex="0">
  <div class="market-panel" on:click|stopPropagation role="dialog">
    <div class="panel-header">
      <h3>Make a Market</h3>
      <button class="close-btn" on:click={handleClose}>✕</button>
    </div>

    <div class="price-inputs">
      <div class="price-group">
        <label for="bid">Bid Price</label>
        <input 
          id="bid"
          type="number" 
          bind:value={bidPrice} 
          step="1"
          min="1"
          class="price-input bid-input"
        />
      </div>

      <div class="spread-display">
        <div class="spread-label">Spread</div>
        <div class="spread-value" class:invalid={spread <= 0}>
          {spread.toFixed(1)}
        </div>
      </div>

      <div class="price-group">
        <label for="ask">Ask Price</label>
        <input 
          id="ask"
          type="number" 
          bind:value={askPrice} 
          step="1"
          min="1"
          class="price-input ask-input"
        />
      </div>
    </div>

    <div class="quote-preview">
      <div class="preview-label">Market Preview:</div>
      <div class="preview-display">
        <span class="bid-preview">{bidPrice}</span>
        <span class="separator">×</span>
        <span class="ask-preview">{askPrice}</span>
      </div>
    </div>

    <div class="panel-actions">
      <button class="btn btn-secondary" on:click={handleClose}>
        Cancel
      </button>
      <button 
        class="btn btn-primary" 
        on:click={handleQuote}
        disabled={spread <= 0}
      >
        Publish
      </button>
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
    z-index: 2000;
  }

  .market-panel {
    background: #2d2d44;
    border-radius: 16px;
    border: 2px solid #4CAF50;
    padding: 24px;
    min-width: 400px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }

  .panel-header h3 {
    margin: 0;
    color: #4CAF50;
    font-size: 1.3rem;
  }

  .close-btn {
    background: none;
    border: none;
    color: #888;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: all 0.2s ease;
  }

  .close-btn:hover {
    color: #fff;
    background: #444;
  }

  .price-inputs {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 20px;
  }

  .price-group {
    flex: 1;
    text-align: center;
  }

  .price-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #ccc;
    font-size: 0.9rem;
  }

  .price-input {
    width: 100%;
    padding: 12px;
    font-size: 1.2rem;
    font-weight: bold;
    text-align: center;
    border: 2px solid #555;
    border-radius: 8px;
    background: #1a1a2e;
    color: white;
    transition: border-color 0.2s ease;
  }

  .price-input:focus {
    outline: none;
    border-color: #4CAF50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
  }

  .bid-input:focus {
    border-color: #F44336;
    box-shadow: 0 0 0 2px rgba(244, 67, 54, 0.2);
  }

  .ask-input:focus {
    border-color: #4CAF50;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
  }

  .price-label {
    margin-top: 6px;
    font-size: 0.8rem;
    color: #888;
  }

  .spread-display {
    text-align: center;
    padding: 0 16px;
  }

  .spread-label {
    font-size: 0.8rem;
    color: #888;
    margin-bottom: 4px;
  }

  .spread-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #FFC107;
    padding: 8px;
    border-radius: 6px;
    background: rgba(255, 193, 7, 0.1);
  }

  .spread-value.invalid {
    color: #F44336;
    background: rgba(244, 67, 54, 0.1);
  }

  .quote-preview {
    background: #1a1a2e;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
    text-align: center;
  }

  .preview-label {
    font-size: 0.9rem;
    color: #888;
    margin-bottom: 8px;
  }

  .preview-display {
    font-size: 1.5rem;
    font-weight: bold;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
  }

  .bid-preview {
    color: #F44336;
    padding: 8px 16px;
    background: rgba(244, 67, 54, 0.1);
    border-radius: 6px;
  }

  .ask-preview {
    color: #4CAF50;
    padding: 8px 16px;
    background: rgba(76, 175, 80, 0.1);
    border-radius: 6px;
  }

  .separator {
    color: #666;
    font-size: 1.2rem;
  }

  .panel-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .panel-actions .btn {
    padding: 12px 24px;
    font-weight: 600;
  }
</style> 