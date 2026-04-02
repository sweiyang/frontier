<script>
  import { onMount } from "svelte";
  import { Megaphone, ChevronLeft, ChevronRight, X } from "lucide-svelte";

  let { banners = [], ondismisschange = () => {}, restored = false } = $props();

  let currentIndex = $state(0);
  let dismissed = $state(false);
  let progressKey = $state(0);
  let transitioning = $state(false);
  let direction = $state(1); // 1 = forward, -1 = backward
  let intervalId = null;

  // Load dismissed state from localStorage
  let dismissedMap = $state(
    JSON.parse(localStorage.getItem("frontier_dismissed_banners") || "{}")
  );

  let visibleBanners = $derived(
    banners.filter((b) => {
      const stored = dismissedMap[b.id];
      if (!stored) return true;
      // Re-show if banner was updated after dismissal
      return b.updated_at && stored !== b.updated_at;
    })
  );

  let currentBanner = $derived(
    visibleBanners.length > 0
      ? visibleBanners[currentIndex % visibleBanners.length]
      : null
  );

  let showBanner = $derived(!dismissed && visibleBanners.length > 0);

  function startTimer() {
    stopTimer();
    if (visibleBanners.length <= 1) return;
    intervalId = setInterval(() => {
      navigate(1);
    }, 5000);
  }

  function stopTimer() {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }

  function navigate(dir) {
    if (visibleBanners.length <= 1) return;
    transitioning = true;
    direction = dir;
    setTimeout(() => {
      currentIndex =
        (currentIndex + dir + visibleBanners.length) % visibleBanners.length;
      progressKey++;
      transitioning = false;
    }, 200);
    stopTimer();
    startTimer();
  }

  function dismiss() {
    // Store all visible banner IDs as dismissed
    const updated = { ...dismissedMap };
    for (const b of visibleBanners) {
      updated[b.id] = b.updated_at || "dismissed";
    }
    dismissedMap = updated;
    localStorage.setItem("frontier_dismissed_banners", JSON.stringify(updated));
    dismissed = true;
    stopTimer();
    ondismisschange(true);
  }

  function restore() {
    // Clear dismissed entries for current banners
    const updated = { ...dismissedMap };
    for (const b of banners) {
      delete updated[b.id];
    }
    dismissedMap = updated;
    localStorage.setItem("frontier_dismissed_banners", JSON.stringify(updated));
    dismissed = false;
    currentIndex = 0;
    progressKey++;
    startTimer();
    ondismisschange(false);
  }

  onMount(() => {
    // Check if banners were already dismissed on mount
    if (visibleBanners.length === 0 && banners.length > 0) {
      dismissed = true;
      ondismisschange(true);
    }
    startTimer();
    return () => stopTimer();
  });

  $effect(() => {
    // Reset index if banners change
    if (visibleBanners.length > 0 && currentIndex >= visibleBanners.length) {
      currentIndex = 0;
    }
  });

  // Handle restore from parent
  $effect(() => {
    if (restored && dismissed) {
      restore();
    }
  });
</script>

{#if showBanner}
  <div class="notification-banner">
    <div class="banner-content">
      <!-- Left: icon + tag + message -->
      <div class="banner-left">
        <div class="megaphone-icon" style="background: {currentBanner?.tag_color || '#ED1C24'}15; color: {currentBanner?.tag_color || '#ED1C24'};">
          <Megaphone size={16} />
        </div>

        <div class="banner-text-area" class:slide-out={transitioning}>
          {#if currentBanner}
            {#key currentBanner.id + "-" + progressKey}
              <div class="banner-text-inner slide-in">
                <span class="banner-tag" style="background: {currentBanner.tag_color || '#ED1C24'}15; color: {currentBanner.tag_color || '#ED1C24'};">{currentBanner.tag}</span>
                <span class="banner-message">
                  {currentBanner.message}
                  {#if currentBanner.link_url}
                    <a
                      href={currentBanner.link_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      class="banner-link"
                      style="color: {currentBanner.tag_color || '#ED1C24'};"
                    >Learn more</a>
                  {/if}
                </span>
              </div>
            {/key}
          {/if}
        </div>
      </div>

      <!-- Right: controls -->
      <div class="banner-right">
        {#if visibleBanners.length > 1}
          <button
            class="nav-btn"
            onclick={() => navigate(-1)}
            title="Previous"
          >
            <ChevronLeft size={16} />
          </button>
          <span class="banner-counter">
            {currentIndex + 1} / {visibleBanners.length}
          </span>
          <button class="nav-btn" onclick={() => navigate(1)} title="Next">
            <ChevronRight size={16} />
          </button>
        {/if}
        <button class="dismiss-btn" onclick={dismiss} title="Dismiss">
          <X size={16} />
        </button>
      </div>
    </div>

    <!-- Progress bar -->
    {#if visibleBanners.length > 1}
      {#key progressKey}
        <div class="progress-track">
          <div class="progress-bar" style="background: {currentBanner?.tag_color || '#ED1C24'};"></div>
        </div>
      {/key}
    {/if}
  </div>
{/if}

<style>
  .notification-banner {
    width: 100%;
    background: var(--bg-primary);
    border-bottom: 1px solid #f3f4f6;
    flex-shrink: 0;
    position: relative;
    z-index: 50;
  }

  .banner-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.625rem 2rem;
    gap: 1rem;
    min-height: 44px;
  }

  .banner-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
    min-width: 0;
    overflow: hidden;
  }

  .megaphone-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .banner-text-area {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    position: relative;
  }

  .banner-text-inner {
    display: flex;
    align-items: center;
    gap: 0.625rem;
  }

  .banner-tag {
    font-size: 0.625rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.125rem 0.5rem;
    border-radius: var(--radius-sm);
    white-space: nowrap;
    flex-shrink: 0;
  }

  .banner-message {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .banner-link {
    text-decoration: none;
    font-weight: 600;
    margin-left: 0.25rem;
  }

  .banner-link:hover {
    text-decoration: underline;
  }

  .banner-right {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    flex-shrink: 0;
  }

  .nav-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    border-radius: var(--radius-sm);
    transition: color 0.15s ease, background 0.15s ease;
  }

  .nav-btn:hover {
    color: var(--text-primary);
    background: var(--bg-hover, rgba(0, 0, 0, 0.04));
  }

  .banner-counter {
    font-size: 0.75rem;
    font-family: "SF Mono", "Fira Code", "Consolas", monospace;
    color: var(--text-secondary);
    min-width: 2.5rem;
    text-align: center;
    user-select: none;
  }

  .dismiss-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    border-radius: var(--radius-sm);
    margin-left: 0.5rem;
    transition: color 0.15s ease, background 0.15s ease;
  }

  .dismiss-btn:hover {
    color: var(--text-primary);
    background: var(--bg-hover, rgba(0, 0, 0, 0.04));
  }

  /* Progress bar */
  .progress-track {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: transparent;
  }

  .progress-bar {
    height: 100%;
    width: 0%;
    animation: progress 5s linear forwards;
  }

  @keyframes progress {
    from {
      width: 0%;
    }
    to {
      width: 100%;
    }
  }

  /* Slide-up animation */
  .slide-in {
    animation: slideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }

  .slide-out {
    animation: slideOut 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes slideOut {
    from {
      opacity: 1;
      transform: translateY(0);
    }
    to {
      opacity: 0;
      transform: translateY(-8px);
    }
  }

  /* Dark mode */
  :global([data-theme="dark"]) .notification-banner {
    border-bottom-color: var(--border-color);
  }


  /* Responsive */
  @media (max-width: 768px) {
    .banner-content {
      padding: 0.5rem 1rem;
    }

    .banner-counter {
      display: none;
    }

    .banner-message {
      font-size: 0.8125rem;
    }
  }
</style>
