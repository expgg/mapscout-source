"""
MapScout v2.5 — Visual Virtual Cursor & Humanized Browser Effects
Injects glowing cursor and click ripples for browser observability and anti-detection.
"""

import time

INJECT_CURSOR_JS = """
if (!document.getElementById('virtual-bot-cursor')) {
    const cursor = document.createElement('div');
    cursor.id = 'virtual-bot-cursor';
    cursor.style.position = 'fixed';
    cursor.style.zIndex = '9999999';
    cursor.style.width = '16px';
    cursor.style.height = '16px';
    cursor.style.borderRadius = '50%';
    cursor.style.background = 'rgba(0, 229, 255, 0.9)';
    cursor.style.border = '2px solid #ffffff';
    cursor.style.boxShadow = '0 0 15px #00e5ff, 0 0 30px #00e5ff';
    cursor.style.pointerEvents = 'none';
    cursor.style.transform = 'translate(-50%, -50%)';
    cursor.style.transition = 'left 0.25s cubic-bezier(0.2, 0.8, 0.2, 1), top 0.25s cubic-bezier(0.2, 0.8, 0.2, 1), transform 0.15s ease';
    cursor.style.top = '120px';
    cursor.style.left = '120px';
    document.body.appendChild(cursor);
    
    window.lastBotActivity = Date.now();
    
    window.botCursorMove = function(x, y) {
        window.lastBotActivity = Date.now();
        cursor.style.left = x + 'px';
        cursor.style.top = y + 'px';
    };
    
    window.botCursorClick = function(x, y) {
        window.lastBotActivity = Date.now();
        cursor.style.left = x + 'px';
        cursor.style.top = y + 'px';
        cursor.style.transform = 'translate(-50%, -50%) scale(0.6)';
        
        const ripple = document.createElement('div');
        ripple.style.position = 'fixed';
        ripple.style.zIndex = '9999998';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.style.width = '14px';
        ripple.style.height = '14px';
        ripple.style.borderRadius = '50%';
        ripple.style.border = '2px solid #00ff88';
        ripple.style.transform = 'translate(-50%, -50%) scale(1)';
        ripple.style.transition = 'all 0.35s ease-out';
        ripple.style.pointerEvents = 'none';
        document.body.appendChild(ripple);
        
        setTimeout(() => {
            ripple.style.transform = 'translate(-50%, -50%) scale(4)';
            ripple.style.opacity = '0';
        }, 20);
        
        setTimeout(() => {
            cursor.style.transform = 'translate(-50%, -50%) scale(1)';
            ripple.remove();
        }, 350);
    };
}
"""

def inject_visual_cursor(driver):
    """Injects virtual glowing bot cursor into active document."""
    try:
        driver.execute_script(INJECT_CURSOR_JS)
    except Exception:
        pass


def move_cursor_to(driver, element, click: bool = False):
    """Moves virtual bot cursor smoothly toward target element and triggers visual ripple."""
    try:
        inject_visual_cursor(driver)
        rect = driver.execute_script("return arguments[0].getBoundingClientRect();", element)
        if rect:
            target_x = int(rect['left'] + rect['width'] / 2)
            target_y = int(rect['top'] + rect['height'] / 2)
            driver.execute_script(f"if (window.botCursorMove) window.botCursorMove({target_x}, {target_y});")
            time.sleep(0.05)
            if click:
                driver.execute_script(f"if (window.botCursorClick) window.botCursorClick({target_x}, {target_y});")
                time.sleep(0.05)
    except Exception:
        pass
