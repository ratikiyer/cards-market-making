<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import GameTable from './components/GameTable.svelte';
  import JoinForm from './components/JoinForm.svelte';

  // Store states
  const playerName = writable('');
  const buyIn = writable(1000);
  const joined = writable(false);
  const pid = writable('');
  const gameState = writable<any>({});
  const connectionStatus = writable('disconnected'); // 'disconnected', 'connecting', 'connected', 'reconnecting', 'error'
  const isInitialLoad = writable(true); // Track if this is the first page load
  const hasLeft = writable(false); // Track if player has left the table
  const toastMessage = writable(''); // For showing notifications
  const joiningStatus = writable(''); // Track joining status

  const backendURL = `http://${window.location.hostname}:8000`;
  const wsURL = `ws://${window.location.hostname}:8000`;
  const tid = 'default';
  let ws: WebSocket;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 10;
  let heartbeatInterval: number;
  let reconnectTimeout: number;

  // Save state to localStorage (debounced)
  let saveTimeout: number;
  function saveToLocalStorage() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
      const state = {
        playerName: $playerName,
        buyIn: $buyIn,
        joined: $joined,
        pid: $pid,
        hasLeft: $hasLeft,
        timestamp: Date.now()
      };
      localStorage.setItem('market-maker-game', JSON.stringify(state));
    }, 100);
  }

  // Load state from localStorage
  function loadFromLocalStorage() {
    try {
      const saved = localStorage.getItem('market-maker-game');
      if (saved) {
        const state = JSON.parse(saved);
        // Only restore if timestamp is recent (within last 24 hours)
        const isRecent = Date.now() - state.timestamp < 24 * 60 * 60 * 1000;
        
        if (isRecent) {
          playerName.set(state.playerName || '');
          buyIn.set(state.buyIn || 1000);
          joined.set(state.joined || false);
          pid.set(state.pid || '');
          hasLeft.set(state.hasLeft || false);
        } else {
          // Clear old data
          clearLocalStorage();
        }
      }
    } catch (error) {
      console.error('Error loading from localStorage:', error);
      clearLocalStorage();
    }
  }

  // Clear localStorage
  function clearLocalStorage() {
    localStorage.removeItem('market-maker-game');
    playerName.set('');
    buyIn.set(1000);
    joined.set(false);
    pid.set('');
    hasLeft.set(false);
  }

  onMount(() => {
    // Load existing session data (for page refreshes)
    loadFromLocalStorage();
    
    // If we were previously joined, try to reconnect silently
    if ($joined && $pid && !$pid.startsWith('temp_')) {
      connectionStatus.set('reconnecting');
      connectWebSocket($pid);
    } else {
      // Always connect with a temporary ID for instant interactivity
      const tempId = generateTempId();
      pid.set(tempId);
      connectWebSocket(tempId);
      isInitialLoad.set(false);
    }
  });

  // Subscribe to changes and save them
  $: if ($joined || $pid || $hasLeft) saveToLocalStorage();

  async function joinTable() {
    // Set joining status for optimistic UI
    joiningStatus.set('connecting');
    
    // If already connected, just send join message
    if (ws && ws.readyState === WebSocket.OPEN) {
      joiningStatus.set('joining');
      sendMessage({ 
        action: 'join', 
        name: $playerName, 
        buy_in: $buyIn 
      });
      return;
    }
    
    // If not connected, establish connection first
    if (!$pid || !$pid.startsWith('temp_')) {
      const tempId = generateTempId();
      pid.set(tempId);
    }
    
    connectWebSocket($pid);
    
    // Wait for connection to establish
    await new Promise(resolve => setTimeout(resolve, 200));
    
    joiningStatus.set('joining');
    
    // Send join request via WebSocket
    sendMessage({ 
      action: 'join', 
      name: $playerName, 
      buy_in: $buyIn 
    });
  }

  function generateTempId() {
    return 'temp_' + Math.random().toString(36).substr(2, 9);
  }

  function connectWebSocket(playerId: string) {
    // Clear any existing connection
    if (ws) {
      ws.close();
    }
    clearTimeout(reconnectTimeout);
    clearInterval(heartbeatInterval);

    // Don't show connecting for reconnections, use reconnecting instead
    if (reconnectAttempts === 0 && !$isInitialLoad) {
      connectionStatus.set('connecting');
    }
    
    ws = new WebSocket(`${wsURL}/ws/${tid}/${playerId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      connectionStatus.set('connected');
      reconnectAttempts = 0;
      isInitialLoad.set(false);
      
      // Set up heartbeat to detect connection issues
      heartbeatInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'ping' }));
        }
      }, 30000);
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'state') {
        // Check if this is a "fresh backend" signal (empty players list when we expect to be joined)
        if (message.players && message.players.length === 0 && $joined && $pid && !$isInitialLoad) {
          console.log('Backend appears to have restarted - need to rejoin');
          handleBackendRestart();
          return;
        }
        
        // Check if we're not in the players list but should be
        if (message.players && message.players.length > 0 && $joined && $pid) {
          const ourPlayer = message.players.find((p: any) => p.pid === $pid);
          if (!ourPlayer) {
            console.log('Player session expired - need to rejoin');
            handleSessionExpired();
            return;
          }
        }
        
        // Check if current player has left status and handle it (fallback)
        if (message.all_players && $joined && $pid) {
          const currentPlayer = message.all_players.find((p: any) => p.pid === $pid);
          if (currentPlayer && currentPlayer.status === 'left') {
            console.log('Player has left the table (fallback detection)');
            // Use the new event-based handler instead of the old one
            handlePlayerEvent({
              event: 'you_left',
              message: 'You have left the table.',
              redirect_to_lobby: true
            });
            return;
          }
        }
        
        gameState.set(message);
      } else if (message.type === 'round') {
        gameState.update(state => ({
          ...state,
          round: message.round,
          community: message.community
        }));
      } else if (message.type === 'trade') {
        console.log('Trade occurred:', message);
        // Don't update gameState here - wait for the full state update
      } else if (message.type === 'quote') {
        console.log('Quote posted:', message);
        // Don't update gameState here - wait for the full state update
      } else if (message.type === 'hand_complete') {
        console.log('Hand complete:', message.message);
        // Could show a brief notification here if desired
      } else if (message.type === 'join_success') {
        // Successfully joined via WebSocket
        console.log('Join successful:', message);
        pid.set(message.pid);
        joined.set(true);
        hasLeft.set(false);
        isInitialLoad.set(false);
        reconnectAttempts = 0;
        joiningStatus.set('');
        showToast(message.message || 'Welcome to the table!', 3000);
        
      } else if (message.type === 'join_error') {
        // Join failed
        console.error('Join error:', message.error);
        joiningStatus.set('');
        showToast(`Error: ${message.error}`, 5000);
        
      } else if (message.type === 'player_event') {
        handlePlayerEvent(message);
      } else if (message.type === 'error') {
        console.error('Server error:', message.detail);
        alert(message.detail);
      } else if (message.type === 'info') {
        console.log('Server info:', message.detail);
        // Could show a toast notification here if desired
      } else if (message.type === 'pong') {
        // Heartbeat response - connection is healthy
      } else if (message.type === 'options_updated') {
        console.log('Options updated:', message);
        showToast(`Game options updated by ${message.updated_by}`, 3000);
      } else if (message.type === 'width_auction_started') {
        console.log('Width auction started:', message);
        showToast('Width auction started! Submit your bid.', 3000);
      } else if (message.type === 'auction_timer_update') {
        // Update auction timer in real-time
        gameState.update(state => ({
          ...state,
          auction_time_remaining: message.time_remaining
        }));
      } else if (message.type === 'width_bid_received') {
        console.log('Width bid received:', message);
        // Could show a notification about bid progress
      } else if (message.type === 'width_auction_complete' || message.type === 'width_auction_timeout') {
        console.log('Width auction complete:', message);
        if (message.result && message.result.winner) {
          showToast(`Auction won by ${message.result.winner_name} with spread ${message.result.winning_width}`, 5000);
        } else {
          showToast('Auction completed with no bids', 3000);
        }
      }
    };
    
    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      clearInterval(heartbeatInterval);
      
      if (!$joined) return; // Don't reconnect if not joined
      
      // Handle different close codes
      if (event.code === 1000) {
        // Normal closure - don't reconnect
        connectionStatus.set('disconnected');
        return;
      }
      
      connectionStatus.set('reconnecting');
      
      // Exponential backoff with jitter
      if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        const baseDelay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 30000);
        const jitter = Math.random() * 1000; // Add randomness to prevent thundering herd
        const delay = baseDelay + jitter;
        
        console.log(`Reconnecting in ${Math.round(delay)}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
        
        reconnectTimeout = setTimeout(() => {
          if ($joined && $pid) {
            connectWebSocket($pid);
          }
        }, delay);
      } else {
        console.log('Max reconnection attempts reached');
        connectionStatus.set('error');
        handleConnectionFailure();
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if ($connectionStatus !== 'reconnecting') {
        connectionStatus.set('error');
      }
    };
  }

  function handleBackendRestart() {
    console.log('Handling backend restart...');
    clearLocalStorage();
    joined.set(false);
    pid.set('');
    connectionStatus.set('disconnected');
    reconnectAttempts = 0;
  }

  function handleSessionExpired() {
    console.log('Session expired, attempting to rejoin...');
    // Try to rejoin automatically with same credentials
    if ($playerName) {
      // Don't force a page refresh, just rejoin silently
      joinTable();
    } else {
      // Only clear state if we can't rejoin
      handleBackendRestart();
    }
  }

  function showToast(message: string, duration: number = 3000) {
    toastMessage.set(message);
    setTimeout(() => toastMessage.set(''), duration);
  }

  function handlePlayerEvent(message: any) {
    console.log('Player event:', message);
    
    if (message.event === 'you_left') {
      // Smooth transition for the player who left
      console.log('You have left the table');
      
      // Show success message
      showToast(message.message || 'You have left the table successfully', 5000);
      
      // Mark that the player has left but keep connection open
      hasLeft.set(true);
      joined.set(false);
      
      // Clear the PID so they can't accidentally rejoin as the same player
      pid.set('');
      
      // Don't close websocket - just transition to lobby state
      if (message.redirect_to_lobby) {
        console.log('Transitioning to lobby...');
      }
      
    } else if (message.event === 'player_left') {
      // Another player left - show notification and update UI smoothly
      console.log(`${message.player_name} left the table`);
      
      // Show toast notification
      showToast(`${message.player_name} left the table`, 3000);
      
    } else if (message.event === 'player_joined') {
      // Another player joined - show notification
      console.log(`${message.player_name} joined the table`);
      
      // Show toast notification
      showToast(`${message.player_name} joined the table`, 3000);
      
    } else if (message.event === 'you_pending_leave') {
      // Current player is pending leave
      console.log('You are pending leave');
      showToast(message.message || 'You will leave after this hand completes', 4000);
      
    } else if (message.event === 'pending_leave') {
      // Another player is pending leave
      console.log(`${message.player_name} will leave after this hand`);
      
      // Show notification that someone is leaving soon
      showToast(`${message.player_name} will leave after this hand completes`, 4000);
    }
  }

  function handlePlayerLeft() {
    console.log('Player has left the table - disconnecting...');
    // Close the WebSocket connection to stop receiving updates
    if (ws) {
      ws.close();
    }
    // Mark that the player has left
    hasLeft.set(true);
    // Update the joined status to show the left state
    joined.set(false);
    // Clear the connection status
    connectionStatus.set('disconnected');
    // Keep playerName and other data for potential rejoin
    // Clear the PID so they can't accidentally rejoin as the same player
    pid.set('');
  }

  function handleConnectionFailure() {
    // Show user-friendly error and option to refresh
    console.log('Max reconnection attempts reached');
    connectionStatus.set('error');
  }

  function sendMessage(action: any) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(action));
    } else {
      console.warn('WebSocket not connected, cannot send message:', action);
      // Don't automatically reconnect on every message send - let the normal reconnection logic handle it
      if ($connectionStatus === 'connected') {
        connectionStatus.set('reconnecting');
      }
    }
  }





  function forceRejoin() {
    clearLocalStorage();
    connectionStatus.set('disconnected');
    if (ws) ws.close();
  }
</script>

<main class="app">
  {#if !$joined}
    {#if $hasLeft}
      <!-- Player has left the table -->
      <div class="left-message">
        <div class="left-content">
          <h2>👋 You have left the table</h2>
          <p>Your game history and final statistics have been recorded</p>
          <button class="btn btn-primary" on:click={() => { hasLeft.set(false); }}>
            Join a New Game
          </button>
        </div>
      </div>
    {:else}
      <JoinForm 
        {playerName}
        {buyIn}
        {joiningStatus}
        onJoin={joinTable}
      />
    {/if}
  {:else}
    <!-- Seamless reconnection handling -->
    {#if $isInitialLoad && $connectionStatus === 'reconnecting'}
      <!-- Silent loading for page refresh -->
      <div class="silent-loading">
        <div class="game-skeleton">
          <div class="skeleton-header"></div>
          <div class="skeleton-table"></div>
        </div>
        <div class="reconnect-indicator">
          <div class="pulse-dot"></div>
          <span>Restoring session...</span>
        </div>
      </div>
    {:else if $connectionStatus === 'connecting'}
      <div class="connection-overlay">
        <div class="connection-message">
          <div class="spinner"></div>
          <p>Joining game...</p>
        </div>
      </div>
    {:else if $connectionStatus === 'reconnecting' && !$isInitialLoad}
      <!-- Non-intrusive reconnection banner -->
      <div class="reconnect-banner">
        <div class="banner-content">
          <div class="spinner small"></div>
          <span>Reconnecting... ({reconnectAttempts}/{maxReconnectAttempts})</span>
        </div>
      </div>
      <GameTable 
        {gameState}
        {pid}
        {connectionStatus}
        {sendMessage}
      />
    {:else if $connectionStatus === 'error'}
      <div class="connection-overlay">
        <div class="connection-message error">
          <p>Connection lost and could not be restored.</p>
          <div class="error-actions">
            <button class="btn btn-primary" on:click={() => window.location.reload()}>
              Refresh Page
            </button>
            <button class="btn btn-secondary" on:click={forceRejoin}>
              Return to Lobby
            </button>
          </div>
        </div>
      </div>
    {:else}
      <!-- Connected - show game with subtle status indicator -->
      {#if $connectionStatus === 'connected'}
        <div class="connection-indicator">
          <div class="status-dot connected"></div>
        </div>
      {/if}
      
      <GameTable 
        {gameState}
        {pid}
        {connectionStatus}
        {sendMessage}
      />
    {/if}
  {/if}
  
  <!-- Toast Notification -->
  {#if $toastMessage}
    <div class="toast-notification">
      <div class="toast-content">
        {$toastMessage}
      </div>
    </div>
  {/if}
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #1a1a2e;
    color: white;
    overflow: hidden;
  }

  .app {
    width: 100vw;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
  }

  .connection-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10000;
  }

  .connection-message {
    background: #2d2d44;
    border-radius: 12px;
    padding: 30px;
    text-align: center;
    border: 1px solid #444;
    min-width: 300px;
  }

  .connection-message.error {
    border-color: #F44336;
  }

  .connection-message p {
    margin: 0 0 20px 0;
    color: #ccc;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #444;
    border-top: 4px solid #4CAF50;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px auto;
  }

  .spinner.small {
    width: 20px;
    height: 20px;
    border-width: 2px;
    margin: 0;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Silent loading for page refresh */
  .silent-loading {
    min-height: 100vh;
    background: #1a1a2e;
    position: relative;
    overflow: hidden;
  }

  .game-skeleton {
    padding: 20px;
    opacity: 0.6;
  }

  .skeleton-header {
    height: 60px;
    background: linear-gradient(90deg, #2d2d44 25%, #3d3d54 50%, #2d2d44 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s infinite;
    border-radius: 8px;
    margin-bottom: 20px;
  }

  .skeleton-table {
    height: 400px;
    background: linear-gradient(90deg, #2d2d44 25%, #3d3d54 50%, #2d2d44 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s infinite;
    border-radius: 12px;
    margin: 0 auto;
    max-width: 800px;
  }

  @keyframes skeleton-loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  .reconnect-indicator {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: rgba(76, 175, 80, 0.9);
    color: white;
    padding: 12px 20px;
    border-radius: 25px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.9rem;
    backdrop-filter: blur(10px);
    z-index: 1000;
  }

  .pulse-dot {
    width: 8px;
    height: 8px;
    background: white;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
  }

  .reconnect-banner {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: linear-gradient(90deg, #ff9800, #ff5722);
    color: white;
    z-index: 1000;
    padding: 8px 0;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
  }

  .banner-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .connection-indicator {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 999;
  }

  .status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #4CAF50;
    box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
    animation: connection-pulse 3s infinite;
  }

  @keyframes connection-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }

  .error-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
    margin-top: 16px;
  }

  :global(*) {
    box-sizing: border-box;
  }

  :global(.btn) {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s ease;
  }

  :global(.btn-primary) {
    background: #4CAF50;
    color: white;
  }

  :global(.btn-primary:hover) {
    background: #45a049;
  }

  :global(.btn-secondary) {
    background: #6c757d;
    color: white;
  }

  :global(.btn-secondary:hover) {
    background: #5a6268;
  }

  :global(.btn-warning) {
    background: #FF9800;
    color: white;
  }

  :global(.btn-warning:hover) {
    background: #F57C00;
  }

  :global(.btn-danger) {
    background: #dc3545;
    color: white;
  }

  :global(.btn-danger:hover) {
    background: #c82333;
  }

  :global(input, select) {
    padding: 8px 12px;
    border: 1px solid #444;
    border-radius: 4px;
    background: #2d2d44;
    color: white;
    font-size: 14px;
  }

  :global(input:focus, select:focus) {
    outline: none;
    border-color: #4CAF50;
  }

  .left-message {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
  }

  .left-content {
    background: #2d2d44;
    border-radius: 12px;
    padding: 48px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    border: 1px solid #444;
    max-width: 500px;
  }

  .left-content h2 {
    margin: 0 0 24px 0;
    color: #4CAF50;
    font-size: 28px;
  }

  .left-content p {
    margin: 16px 0;
    color: #ccc;
    font-size: 16px;
    line-height: 1.5;
  }

  .left-content .btn {
    margin-top: 24px;
    padding: 12px 24px;
    font-size: 16px;
  }

  /* Toast Notification */
  .toast-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    animation: slideInRight 0.3s ease-out, fadeOut 0.3s ease-in 2.7s;
    pointer-events: none;
  }

  .toast-content {
    background: rgba(34, 34, 34, 0.95);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border-left: 4px solid #10b981;
    font-size: 14px;
    max-width: 300px;
    word-wrap: break-word;
  }

  @keyframes slideInRight {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes fadeOut {
    from {
      opacity: 1;
    }
    to {
      opacity: 0;
    }
  }
</style>
