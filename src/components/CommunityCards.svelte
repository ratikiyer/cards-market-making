<script lang="ts">
  import Card from './Card.svelte';

  export let cards: string[];
  export let round: number;
</script>

<div class="community-area">
  <div class="cards-container">
    {#each Array(3) as _, index}
      {#if cards[index]}
        <Card card={cards[index]} hidden={false} size="large" />
      {:else}
        <Card card="" hidden={true} size="large" />
      {/if}
    {/each}
  </div>
  
  {#if round > 0}
    <div class="round-indicator">
      Round {round} of 4
    </div>
  {/if}
</div>

<style>
  .community-area {
    text-align: center;
    padding: 20px;
  }

  .cards-container {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-bottom: 16px;
  }

  .round-indicator {
    color: #ccc;
    font-size: 1rem;
    font-weight: 500;
  }
</style> 