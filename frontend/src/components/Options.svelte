<script lang="ts">
  export let gameState: any;
  export let sendMessage: (action: any) => void;
  export let onClose: () => void = () => {};

  let auctionEnabled = gameState?.auction_enabled || false;
  let maxSpreads = gameState?.max_spreads ? [...gameState.max_spreads] : [10, 10, 10, 10];
  let initialized = false;

  // Only update local state from gameState on initial load
  $: if (gameState && !initialized) {
    auctionEnabled = gameState.auction_enabled || false;
    maxSpreads = gameState.max_spreads ? [...gameState.max_spreads] : [10, 10, 10, 10];
    initialized = true;
  }

  function handleSave() {
    // Validate spreads only if auction is disabled (when spreads are used)
    if (!auctionEnabled) {
      for (let i = 0; i < maxSpreads.length; i++) {
        if (maxSpreads[i] <= 0 || !Number.isFinite(maxSpreads[i])) {
          alert(`Round ${i} spread must be a positive number`);
          return;
        }
      }
    }

    sendMessage({
      action: "update_options",
      auction_enabled: auctionEnabled,
      max_spreads: maxSpreads
    });
    
    onClose();
  }

  function handleClose() {
    onClose();
  }
</script>

<div class="modal-overlay" on:click={handleClose} on:keydown={(e) => e.key === 'Escape' && handleClose()} role="button" tabindex="0">
  <div class="options-panel" on:click|stopPropagation role="dialog">
    <div class="panel-header">
      <h3>Game Options</h3>
      <button class="close-btn" on:click={handleClose}>✕</button>
    </div>

    <div class="options-content">
      <div class="option-group">
        <label class="toggle-label">
          <input 
            type="checkbox" 
            bind:checked={auctionEnabled}
            class="toggle-checkbox"
          />
          <span class="toggle-slider"></span>
          <span class="toggle-text">Enable Auction for Market Width</span>
        </label>
        <p class="option-description">
          When enabled, players bid on the maximum spread they're willing to make markets with. 
          The lowest bidder becomes the market maker for that hand.
        </p>
      </div>

      <div class="option-group">
        <h4>Maximum Spreads by Round</h4>
        <p class="option-description">
          Set the maximum allowed spread (Ask - Bid) for each round when auction mode is disabled.
        </p>
        
        <div class="spreads-grid">
          {#each maxSpreads as spread, index}
            <div class="spread-input-group">
              <label for="spread-{index}">Round {index}</label>
              <input 
                id="spread-{index}"
                type="number" 
                bind:value={spread}
                min="0.1"
                step="0.1"
                class="spread-input"
                disabled={auctionEnabled}
              />
            </div>
          {/each}
        </div>
      </div>
    </div>

    <div class="panel-actions">
      <button class="btn btn-secondary" on:click={handleClose}>
        Cancel
      </button>
      <button 
        class="btn btn-primary" 
        on:click={handleSave}
      >
        Save Options
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
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    backdrop-filter: blur(3px);
  }

  .options-panel {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 2px solid #4a90e2;
    border-radius: 16px;
    padding: 24px;
    width: 500px;
    max-width: 90vw;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    border-bottom: 1px solid #333;
    padding-bottom: 12px;
  }

  .panel-header h3 {
    color: #e0e0e0;
    margin: 0;
    font-size: 1.4rem;
    font-weight: 600;
  }

  .close-btn {
    background: none;
    border: none;
    color: #999;
    font-size: 1.5rem;
    cursor: pointer;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    transition: all 0.2s ease;
  }

  .close-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
  }

  .options-content {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .option-group {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 20px;
  }

  .option-group h4 {
    color: #e0e0e0;
    margin: 0 0 8px 0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .option-description {
    color: #b0b0b0;
    font-size: 0.9rem;
    margin: 8px 0;
    line-height: 1.4;
  }

  .toggle-label {
    display: flex;
    align-items: center;
    cursor: pointer;
    gap: 12px;
  }

  .toggle-checkbox {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
  }

  .toggle-slider {
    position: relative;
    width: 50px;
    height: 24px;
    background: #333;
    border-radius: 12px;
    transition: background 0.3s ease;
  }

  .toggle-slider::before {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    background: #fff;
    border-radius: 50%;
    top: 3px;
    left: 3px;
    transition: transform 0.3s ease;
  }

  .toggle-checkbox:checked + .toggle-slider {
    background: #4a90e2;
  }

  .toggle-checkbox:checked + .toggle-slider::before {
    transform: translateX(26px);
  }

  .toggle-text {
    color: #e0e0e0;
    font-weight: 500;
  }

  .spreads-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 16px;
    margin-top: 12px;
  }

  .spread-input-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .spread-input-group label {
    color: #b0b0b0;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .spread-input {
    background: #2a2a3e;
    border: 1px solid #444;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 1rem;
    transition: all 0.2s ease;
  }

  .spread-input:focus {
    outline: none;
    border-color: #4a90e2;
    box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
  }

  .spread-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .panel-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid #333;
  }

  .btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 100px;
  }

  .btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #e0e0e0;
  }

  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  .btn-primary {
    background: #4a90e2;
    color: white;
  }

  .btn-primary:hover {
    background: #357abd;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
  }
</style> 