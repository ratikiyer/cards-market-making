<script lang="ts">
  import type { Writable } from 'svelte/store';
  
  export let playerName: Writable<string>;
  export let buyIn: Writable<number>;
  export let joiningStatus: Writable<string>;
  export let onJoin: () => void;

  let errorMessage = '';

  function handleJoin() {
    errorMessage = '';
    
    if (!$playerName.trim()) {
      errorMessage = 'Player name is required';
      return;
    }
    
    if ($playerName.trim().length > 20) {
      errorMessage = 'Player name must be 20 characters or less';
      return;
    }

    if (!$buyIn || $buyIn < 1 || $buyIn > 10000 || !Number.isInteger($buyIn)) {
      errorMessage = 'Buy-in must be a whole number between 1 and 10,000';
      return;
    }
    
    onJoin();
  }

  function validateBuyIn(event: Event) {
    const target = event.target as HTMLInputElement;
    const value = parseInt(target.value);
    
    if (isNaN(value)) {
      $buyIn = 1;
    } else if (value < 1) {
      $buyIn = 1;
    } else if (value > 10000) {
      $buyIn = 10000;
    } else {
      $buyIn = value;
    }
  }
</script>

<div class="join-container">
  <div class="join-card">
    <div class="card-header">
      <h1>Cards Market Making Game</h1>
    </div>

    {#if errorMessage}
      <div class="error-message">
        ⚠️ {errorMessage}
      </div>
    {/if}

    <form on:submit|preventDefault={handleJoin} class="join-form">
      <div class="form-group">
        <label for="name">Player Name</label>
        <input 
          id="name"
          type="text" 
          bind:value={$playerName} 
          placeholder="Enter your name..."
          maxlength="20"
          required 
        />
      </div>

      <div class="form-group">
        <label for="buyIn">Buy-in Amount</label>
        <div class="buy-in-container">
          <span class="currency-symbol">$</span>
          <input 
            id="buyIn"
            type="number" 
            bind:value={$buyIn}
            on:input={validateBuyIn}
            min="1"
            max="10000"
            step="1"
            placeholder="1000"
            required 
          />
        </div>
        <div class="buy-in-range">
          <small>Enter amount between $1 - $10,000</small>
        </div>
      </div>

      <button type="submit" class="btn btn-primary join-btn" disabled={$joiningStatus !== ''}>
        {#if $joiningStatus === 'connecting'}
          <span class="spinner"></span> Connecting...
        {:else if $joiningStatus === 'joining'}
          <span class="spinner"></span> Joining...
        {:else}
          Join Table
        {/if}
      </button>
    </form>

    <div class="how-to-play">
      <h3>How to Play</h3>
      <ul>
        <li><strong>Objective:</strong> Trade on the sum of all cards in play (your cards & community cards)</li>
        <li><strong>Card Values:</strong> A=1, J=11, Q=12, K=13, rest are face value</li>
        <li><strong>Market Maker:</strong> Rotates each hand. This player quotes bid/ask prices for others to trade</li>
        <li><strong>4 Rounds:</strong> Your cards → 1st community → 2nd community → 3rd community</li>
        <li><strong>Trading:</strong> Buy and sell on the market maker's quote</li>
      </ul>
    </div>
  </div>
</div>

<style>
  .join-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }

  .join-card {
    background: #2d2d44;
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    border: 1px solid #444;
    max-width: 700px;
    width: 100%;
  }

  .card-header {
    text-align: center;
    margin-bottom: 30px;
  }

  .card-header h1 {
    color: #4CAF50;
    margin: 0 0 10px 0;
    font-size: 2.2rem;
  }

  .card-header p {
    color: #ccc;
    margin: 0;
    font-size: 1.1rem;
  }

  .error-message {
    background: #f44336;
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 0.9rem;
    text-align: center;
  }

  .join-form {
    margin-bottom: 30px;
  }

  .form-group {
    margin-bottom: 24px;
  }

  .form-group label {
    display: block;
    color: #ccc;
    margin-bottom: 8px;
    font-weight: 600;
  }

  .form-group input {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #444;
    border-radius: 8px;
    background: #1a1a2e;
    color: #fff;
    font-size: 16px;
    transition: border-color 0.3s ease;
  }

  .form-group input:focus {
    outline: none;
    border-color: #4CAF50;
  }

  .buy-in-container {
    position: relative;
    display: flex;
    align-items: center;
  }

  .currency-symbol {
    position: absolute;
    left: 16px;
    color: #4CAF50;
    font-weight: bold;
    font-size: 16px;
    z-index: 1;
    pointer-events: none;
  }

  .buy-in-container input {
    padding-left: 40px;
  }

  .buy-in-range {
    margin-top: 6px;
  }

  .buy-in-range small {
    color: #888;
    font-size: 0.8rem;
  }

  .join-btn {
    width: 100%;
    padding: 16px;
    font-size: 1.1rem;
    font-weight: 600;
    border-radius: 8px;
    margin-top: 10px;
  }

  .join-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-right: 8px;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .how-to-play {
    border-top: 1px solid #444;
    padding-top: 24px;
  }

  .how-to-play h3 {
    color: #4CAF50;
    margin: 0 0 16px 0;
    font-size: 1.2rem;
  }

  .how-to-play ul {
    color: #ccc;
    margin: 0;
    padding-left: 20px;
    line-height: 1.6;
  }

  .how-to-play li {
    margin-bottom: 8px;
    font-size: 0.9rem;
  }

  .how-to-play strong {
    color: #fff;
  }
</style> 