<script lang="ts">
  export let card: string = '';
  export let hidden: boolean = false;
  export let size: 'small' | 'medium' | 'large' = 'medium';

  function getCardValue(c: string): string {
    if (!c) return '';
    return c[0] === 'T' ? '10' : c[0];
  }
  function getSuitSymbol(c: string): string {
    if (!c) return '';
    switch (c[1]) {
      case 'H': return '♥';
      case 'D': return '♦';
      case 'C': return '♣';
      case 'S': return '♠';
    }
    return '';
  }
  function getSuitColor(c: string): string {
    if (!c) return '#000';
    return (c[1] === 'H' || c[1] === 'D') ? '#dc3545' : '#000';
  }

  $: rank      = getCardValue(card);
  $: suit      = getSuitSymbol(card);
  $: suitColor = getSuitColor(card);
</script>

{#if hidden}
  <div class="card-back {size}">
    <div class="back-pattern"></div>
  </div>
{:else}
  <div class="card-face {size}" style="color: {suitColor}">
    <div class="rank">{rank}</div>
    <div class="suit">{suit}</div>
  </div>
{/if}

<style>
  /* base card */
  .card-face,
  .card-back {
    position: relative;
    border-radius: 12px;
    border: 1px solid #ccc;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    overflow: hidden;
    background: white;
    font-family: sans-serif;
  }

  /* back pattern */
  .card-back {
    background: linear-gradient(135deg, #a0404a, #6b2c32);
    border: 1.5px solid white;
  }
  .back-pattern {
    width:100%; height:100%;
    background-image:
      radial-gradient(circle at 25% 25%, rgba(255,255,255,0.1) 2px, transparent 2px),
      radial-gradient(circle at 75% 75%, rgba(255,255,255,0.1) 2px, transparent 2px);
    background-size:8px 8px;
  }

  /* rank in top-left */
  .card-face .rank {
    position: absolute;
    top: 8%;
    left: 8%;
    font-weight: bold;
  }

  /* suit centered */
  .card-face .suit {
    position: absolute;
    top: 70%;
    left: 67%;
    transform: translate(-50%, -50%);
    opacity: 0.9;
  }

  /* sizes */
  .small {
    width: 32px;  height: 44px;
  }
  .small .rank { font-size: 0.65rem; }
  .small .suit { font-size: 1rem; }

  .medium {
    width: 52px;  height: 72px;
  }
  .medium .rank { font-size: 1.5rem; }
  .medium .suit { font-size: 1.8rem; }

  .large {
    width: 75px;  height: 105px;
  }
  .large .rank { font-size: 1.9rem; }
  .large .suit { font-size: 2.5rem; /* just a bit larger than medium */ }
</style>
