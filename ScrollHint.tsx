import { useCallback, useEffect, useRef } from "react";
import { motion, useScroll, useMotionValueEvent } from "motion/react";

// --- Hook: auto-snap to nearest section when user scrolls past 50% ---

export function useScrollSnap(containerRef: React.RefObject<HTMLElement | null>) {
  const isSnapping = useRef(false);
  const scrollTimeout = useRef<ReturnType<typeof setTimeout>>(null);

  const snapToNearest = useCallback(() => {
    const container = containerRef.current;
    if (!container || isSnapping.current) return;

    const sections = Array.from(
      container.querySelectorAll<HTMLElement>("[data-snap-section]")
    );
    if (!sections.length) return;

    const scrollTop = container.scrollTop;
    const viewportH = container.clientHeight;

    // Find which section the user is currently inside
    for (let i = 0; i < sections.length; i++) {
      const sectionTop = sections[i].offsetTop;
      const sectionH = sections[i].offsetHeight;
      const sectionBottom = sectionTop + sectionH;

      // User is within this section's range
      if (scrollTop >= sectionTop && scrollTop < sectionBottom) {
        const progress = (scrollTop - sectionTop) / sectionH;
        let targetTop: number;

        if (progress > 0.5 && i < sections.length - 1) {
          // Past halfway → snap to next section
          targetTop = sections[i + 1].offsetTop;
        } else {
          // Before halfway → snap back to current section top
          targetTop = sectionTop;
        }

        // Only snap if we're not already at the target
        if (Math.abs(scrollTop - targetTop) > 2) {
          isSnapping.current = true;
          container.scrollTo({ top: targetTop, behavior: "smooth" });
          // Release lock after animation completes
          setTimeout(() => {
            isSnapping.current = false;
          }, 600);
        }
        break;
      }
    }
  }, [containerRef]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      if (isSnapping.current) return;
      // Debounce: snap after user stops scrolling for 150ms
      if (scrollTimeout.current) clearTimeout(scrollTimeout.current);
      scrollTimeout.current = setTimeout(snapToNearest, 150);
    };

    container.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      container.removeEventListener("scroll", handleScroll);
      if (scrollTimeout.current) clearTimeout(scrollTimeout.current);
    };
  }, [containerRef, snapToNearest]);
}

// --- ScrollHint component ---

interface ScrollHintProps {
  label?: string;
  onClick?: () => void;
  className?: string;
}

export default function ScrollHint({
  label = "SCROLL TO DASHBOARD",
  onClick,
  className = "",
}: ScrollHintProps) {
  const handleClick = () => {
    if (onClick) {
      onClick();
      return;
    }
    const parent = document.querySelector("[data-scroll-hint-parent]");
    if (parent?.nextElementSibling) {
      parent.nextElementSibling.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <motion.div
      className={`absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3 cursor-pointer select-none ${className}`}
      onClick={handleClick}
      animate={{ opacity: [0.5, 1, 0.5] }}
      transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      data-scroll-hint-parent
    >
      {/* Capsule track — mouse/trackpad silhouette */}
      <div className="relative w-6 h-10 rounded-full border border-slate-600/40 overflow-hidden">
        {/* Scan line */}
        <motion.div
          className="absolute left-1 right-1 h-[2px] rounded-full bg-[#EE2E24] shadow-[0_0_8px_rgba(238,46,36,0.4)]"
          animate={{ top: ["20%", "70%"] }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "linear",
            repeatType: "loop",
          }}
        />
      </div>

      {/* Label */}
      <span className="text-[10px] font-medium uppercase tracking-[0.25em] text-slate-500">
        {label}
      </span>
    </motion.div>
  );
}
