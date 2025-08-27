<script lang="ts">
  import Card from './Card.svelte';
  
  export let gameState: any;
  export let pid: string;
  export let sendMessage: (action: any) => void;

  let bidWidth = 5.0;
  let hasSubmittedBid = false;

  $: timeRemaining = Math.max(0, Math.floor(gameState?.auction_time_remaining || 0));
  $: bidsReceived = gameState?.auction_bids_count || 0;
  $: totalEligible = gameState?.eligible_makers?.length || 0;
  $: isEligible = gameState?.eligible_makers?.includes(pid) || false;
  $: currentPlayer = gameState?.players?.find((p: any) => p.pid === pid);
  $: playerCards = currentPlayer?.cards || [];
  $: communityCards = gameState?.community || [];
  $: currentRound = gameState?.round || 0;

  // Check if we've already submitted a bid by seeing if our bids count changed
  let lastBidsCount = 0;
  $: {
    if (bidsReceived > lastBidsCount && lastBidsCount > 0 && isEligible) {
      hasSubmittedBid = true;
    }
    lastBidsCount = bidsReceived;
  }

  function submitBid() {
    if (bidWidth <= 0) {
      alert('Bid width must be positive');
      return;
    }

    sendMessage({
      action: "submit_width_bid",
      width: bidWidth
    });
    
    hasSubmittedBid = true;
  }

  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  $: progressPercent = Math.max(0, Math.min(100, (timeRemaining / 30) * 100));
</script>

<div class="auction-overlay">
  <div class="auction-panel">
    <div class="auction-header">
      <h3>Market Width Auction</h3>
      <div class="timer" class:urgent={timeRemaining < 10}>
        <div class="timer-bar">
          <div class="timer-progress" style="width: {progressPercent}%"></div>
        </div>
        <span class="timer-text">{formatTime(timeRemaining)}</span>
      </div>
    </div>

    <div class="auction-info">
      <p>Bid on the maximum spread you're willing to make markets with.</p>
      <p><strong>Lowest bid wins</strong> and becomes the market maker for this hand.</p>
      
      <div class="bid-status">
        <span class="bids-count">{bidsReceived} / {totalEligible} players have bid</span>
      </div>
    </div>

    <!-- Cards Display Section -->
    <div class="cards-section">
      <div class="player-cards">
        <h4>Your Hand</h4>
        <div class="hand-cards">
          {#each playerCards as card}
            <Card {card} size="small" />
          {/each}
        </div>
      </div>
      
      {#if communityCards.length > 0}
        <div class="community-cards">
          <h4>Community Cards (Round {currentRound + 1})</h4>
          <div class="community-cards-display">
            {#each communityCards as card}
              <Card {card} size="small" />
            {/each}
          </div>
        </div>
      {/if}
    </div>

    {#if !isEligible}
      <div class="ineligible-message">
        <p>You are not eligible to bid in this auction.</p>
        <small>You may have timed out in a previous auction.</small>
      </div>
    {:else if hasSubmittedBid}
      <div class="bid-submitted">
        <div class="submitted-icon">✓</div>
        <p>Your bid has been submitted!</p>
        <p class="bid-amount">Bid Width: {bidWidth}</p>
        <small>Waiting for other players...</small>
      </div>
    {:else}
      <div class="bid-input-section">
        <label for="bid-width">Your Maximum Spread Bid</label>
        <div class="bid-input-group">
          <input 
            id="bid-width"
            type="number" 
            bind:value={bidWidth}
            min="0.1"
            step="0.1"
            class="bid-input"
            disabled={timeRemaining <= 0}
          />
          <button 
            class="submit-bid-btn" 
            on:click={submitBid}
            disabled={timeRemaining <= 0 || bidWidth <= 0}
          >
            Submit Bid
          </button>
        </div>
        <small class="input-help">
          Enter the maximum spread (Ask - Bid) you're willing to commit to.
        </small>
      </div>
    {/if}

    {#if timeRemaining <= 0}
      <div class="timeout-message">
        <p>⏰ Time's up! Resolving auction...</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .auction-overlay {
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
    backdrop-filter: blur(5px);
  }

  .auction-panel {
    background: linear-gradient(135deg, #2a1810 0%, #1a1a2e 100%);
    border: 3px solid #ff8c42;
    border-radius: 20px;
    padding: 30px;
    width: 450px;
    max-width: 90vw;
    text-align: center;
    box-shadow: 0 25px 50px rgba(255, 140, 66, 0.3);
    animation: slideIn 0.3s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-30px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  .auction-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 10px;
  }

  .auction-header h3 {
    color: #ff8c42;
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
  }

  .timer {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .timer-bar {
    width: 80px;
    height: 8px;
    background: #333;
    border-radius: 4px;
    overflow: hidden;
  }

  .timer-progress {
    height: 100%;
    background: #4caf50;
    transition: width 1s linear;
  }

  .timer.urgent .timer-progress {
    background: #f44336;
    animation: pulse 0.5s infinite alternate;
  }

  @keyframes pulse {
    from { opacity: 1; }
    to { opacity: 0.6; }
  }

  .timer-text {
    color: #e0e0e0;
    font-weight: 600;
    font-family: monospace;
  }

  .timer.urgent .timer-text {
    color: #f44336;
  }

  .auction-info {
    background: rgba(255, 140, 66, 0.1);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 20px;
    border: 1px solid rgba(255, 140, 66, 0.3);
  }

  .auction-info p {
    color: #e0e0e0;
    margin: 0 0 8px 0;
    line-height: 1.4;
  }

  .bid-status {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid rgba(255, 140, 66, 0.3);
  }

  .bids-count {
    color: #ff8c42;
    font-weight: 600;
    font-size: 1.1rem;
  }

  .ineligible-message {
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid rgba(244, 67, 54, 0.3);
    border-radius: 12px;
    padding: 20px;
    color: #ffcdd2;
  }

  .ineligible-message p {
    margin: 0 0 8px 0;
    font-weight: 600;
  }

  .ineligible-message small {
    color: #ef9a9a;
  }

  .bid-submitted {
    background: rgba(76, 175, 80, 0.1);
    border: 1px solid rgba(76, 175, 80, 0.3);
    border-radius: 12px;
    padding: 24px;
    color: #c8e6c9;
  }

  .submitted-icon {
    font-size: 3rem;
    color: #4caf50;
    margin-bottom: 12px;
  }

  .bid-submitted p {
    margin: 0 0 8px 0;
  }

  .bid-amount {
    font-weight: 700;
    font-size: 1.2rem;
    color: #4caf50 !important;
  }

  .bid-submitted small {
    color: #a5d6a7;
  }

  .bid-input-section {
    text-align: left;
  }

  .bid-input-section label {
    display: block;
    color: #e0e0e0;
    font-weight: 600;
    margin-bottom: 8px;
  }

  .bid-input-group {
    display: flex;
    gap: 12px;
    margin-bottom: 8px;
  }

  .bid-input {
    flex: 1;
    background: #2a2a3e;
    border: 2px solid #444;
    border-radius: 8px;
    padding: 12px 16px;
    color: #e0e0e0;
    font-size: 1.1rem;
    font-weight: 600;
    transition: all 0.2s ease;
  }

  .bid-input:focus {
    outline: none;
    border-color: #ff8c42;
    box-shadow: 0 0 0 3px rgba(255, 140, 66, 0.2);
  }

  .submit-bid-btn {
    background: linear-gradient(135deg, #ff8c42 0%, #ff6b35 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
  }

  .submit-bid-btn:hover:not(:disabled) {
    background: linear-gradient(135deg, #ff6b35 0%, #ff5722 100%);
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(255, 140, 66, 0.4);
  }

  .submit-bid-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  .input-help {
    color: #b0b0b0;
    font-size: 0.85rem;
    line-height: 1.3;
  }

  .timeout-message {
    background: rgba(255, 193, 7, 0.1);
    border: 1px solid rgba(255, 193, 7, 0.3);
    border-radius: 12px;
    padding: 16px;
    color: #fff3c4;
    margin-top: 16px;
  }

  .timeout-message p {
    margin: 0;
    font-weight: 600;
  }

  /* Cards Section Styles */
  .cards-section {
    background: rgba(255, 140, 66, 0.05);
    border-radius: 12px;
    padding: 16px;
    margin: 16px 0;
    border: 1px solid rgba(255, 140, 66, 0.2);
  }

  .player-cards, .community-cards {
    margin-bottom: 12px;
  }

  .player-cards h4, .community-cards h4 {
    color: #ff8c42;
    margin: 0 0 8px 0;
    font-size: 1rem;
    font-weight: 600;
    text-align: center;
  }

  .hand-cards, .community-cards-display {
    display: flex;
    gap: 8px;
    justify-content: center;
    flex-wrap: wrap;
  }

  .community-cards {
    border-top: 1px solid rgba(255, 140, 66, 0.2);
    padding-top: 12px;
  }
</style> 