
if (window.__MESSAGE_WATCHER_LOADED__) {
    console.log("⚠ Watcher already injected, skipping.");
} else {
    window.__MESSAGE_WATCHER_LOADED__ = true;
    window.__MESSAGE_WATCHER_RESULT__ = [];

    // Hàm kiểm tra một thẻ a có icon mới hay không
    function evaluateATag(aTag) {
        if (!aTag) return;
        const href = aTag.getAttribute("href");
        if (!href) return;

        const hasIcon = aTag.querySelector('div[role="button"][aria-hidden="true"]');

        if (hasIcon) {
            if (!window.__MESSAGE_WATCHER_RESULT__.includes(href)) {
                window.__MESSAGE_WATCHER_RESULT__.push(href);
                console.log("🔔 New message detected:", href);
            }
        }
    }

    // Hàm kiểm tra khi có một node mới xuất hiện bên trong <a>
    function checkNodeForIcons(node) {
        // Node chính là icon mới
        if (node.matches?.('div[role="button"][aria-hidden="true"]')) {
            const parentA = node.closest('a[href^="/messages/"]');
            if (parentA) evaluateATag(parentA);
        }

        // Node chứa icon bên trong nó
        const icons = node.querySelectorAll?.('div[role="button"][aria-hidden="true"]');
        if (icons && icons.length > 0) {
            icons.forEach(icon => {
                const parentA = icon.closest('a[href^="/messages/"]');
                if (parentA) evaluateATag(parentA);
            });
        }
    }

    // Tìm các <a> có sẵn khi script chạy
    document.querySelectorAll('a[href^="/messages/"]').forEach(a => {
        evaluateATag(a);
    });

    // Theo dõi toàn bộ trang
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(node => {
                if (node.nodeType !== 1) return;

                // Nếu node chính là <a>
                if (node.matches?.('a[href^="/messages/"]')) {
                    evaluateATag(node);
                }

                // Bất kỳ node mới nào cũng có thể chứa icon
                checkNodeForIcons(node);
            });
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });

    console.log("✅ Message watcher activated.");

    // Hàm hỗ trợ lấy text từ một node (bao gồm alt text của ảnh)
    window.getText = function(node) {
        let result = "";

        node.childNodes.forEach(child => {
            if (child.nodeType === Node.TEXT_NODE) {
                result += child.textContent;
            } else if (child.nodeType === Node.ELEMENT_NODE) {
                if (child.tagName === "IMG" && child.alt) {
                    result += child.alt;
                } else if (child.tagName === "BR") {
                    result += "\n";
                } else {
                    result += getText(child);
                }
            }
        });

        return result;
    }
}