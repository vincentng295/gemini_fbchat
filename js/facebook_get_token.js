    let accessToken = null;

    const resources = performance.getEntriesByType("resource");

    for (const r of resources) {
        if (r.name.includes("access_token=")) {
            const m = r.name.match(/access_token=([^&]+)/);
            if (m) {
                accessToken = decodeURIComponent(m[1]);
                break;
            }
        }
    }

    return accessToken;