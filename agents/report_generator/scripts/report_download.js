// Client-side report ZIP generator
// Loads JSZip dynamically (CDN) if not present, then exposes createReportZip()
(function () {
    const JSZIP_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';

    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const existing = document.querySelector(`script[src="${src}"]`);
            if (existing) {
                if (existing.hasAttribute('data-loaded')) return resolve();
                existing.addEventListener('load', () => resolve());
                existing.addEventListener('error', (e) => reject(e));
                return;
            }
            const s = document.createElement('script');
            s.src = src;
            s.async = true;
            s.addEventListener('load', () => {
                s.setAttribute('data-loaded', '1');
                resolve();
            });
            s.addEventListener('error', (e) => reject(e));
            document.head.appendChild(s);
        });
    }

    async function ensureJSZip() {
        if (window.JSZip) return;
        await loadScript(JSZIP_CDN);
        if (!window.JSZip) throw new Error('JSZip failed to load');
    }

    window.createReportZip = async function createReportZip() {
        const btn = document.getElementById('download-zip-btn');
        if (!btn) return;
        btn.disabled = true;
        const origText = btn.innerText;
        btn.innerText = 'Preparazione...';
        let metadata = {};
        try {
            const metaEl = document.getElementById('report-metadata');
            if (metaEl) metadata = JSON.parse(metaEl.textContent || '{}');
        } catch (e) {
            console.warn('Invalid metadata JSON', e);
            metadata = {};
        }

        try {
            await ensureJSZip();
            const zip = new window.JSZip();
            const htmlContent = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
            zip.file('report.html', htmlContent);
            zip.file('metadata.json', JSON.stringify(metadata, null, 2));

            const content = await zip.generateAsync({ type: 'blob' });
            const safeTitle = (metadata.title || 'ai_risk_report').replace(/[^a-z0-9\-_.]/gi, '_').toLowerCase();
            const ts = new Date().toISOString().slice(0,19).replace(/[:T]/g,'-');
            const filename = `${safeTitle}_${ts}.zip`;

            const link = document.createElement('a');
            link.href = URL.createObjectURL(content);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(link.href);
        } catch (err) {
            console.error('ZIP creation failed', err);
            alert('Error creating ZIP file: ' + err.message);
        } finally {
            btn.disabled = false;
            btn.innerText = origText;
        }
    };

})();
