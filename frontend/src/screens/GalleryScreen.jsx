import React, { useEffect, useState } from "react";
import api from "../../api/api";
import "../styles/Gallery.css";

const BACKEND_ORIGIN = api.defaults.baseURL.replace(/\/api\/?$/, "");
const toAbs = (u) => (u && u.startsWith("/media/")) ? BACKEND_ORIGIN + u : u;

export default function Gallery({ sessionId: propSessionId }) {
    // sessionId can come from router params or props. For quick test, try localStorage fallback.
    const urlId = (() => {
        const m = window.location.pathname.match(/\/gallery\/(\d+)/);
        return m ? m[1] : null;
    })();
    const sessionId = propSessionId || urlId || localStorage.getItem("sessionId");

    const [items, setItems] = useState([]);
    const [active, setActive] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!sessionId) return;
        setLoading(true);
        api.get(`/gallery/${sessionId}`)
            .then((res) => setItems(res.data.items || []))
            .finally(() => setLoading(false));
    }, [sessionId]);

    return (
        <div className="gal">
            {loading && <div className="gal-loading">Loading…</div>}

            {!loading && items.length === 0 && (
                <div className="gal-empty">No entries yet for this session.</div>
            )}

            {!loading && items.length > 0 && (
                <div className="gal-grid">
                    {items.map((g) => (
                        <button key={`${g.turn_id}-${g.option_id}`} className="gal-card" onClick={() => setActive(g)}>
                            {g.image_url
                                ? <img className="gal-thumb" loading="lazy" src={toAbs(g.image_url)} alt={g.option_text || `Year ${g.year}`} />
                                : <div className="gal-thumb gal-thumb--empty">No image</div>
                            }
                            <div className="gal-meta">
                                <div className="gal-year">{g.year}</div>
                                {/* Decision text (was A/B); no labels shown */}
                                <div className="gal-decision clamp-2">{g.option_text}</div>
                            </div>
                        </button>
                    ))}
                </div>
            )}

            {active && (
                <div className="gal-modal" onClick={() => setActive(null)}>
                    <div className="gal-modal-body" onClick={(e) => e.stopPropagation()}>
                        <button className="gal-close" onClick={() => setActive(null)} aria-label="Close">×</button>

                        {/* Image constrained so it’s not massive */}
                        {active.image_url && (
                            <img
                                className="gal-modal-img"
                                src={toAbs(active.image_url)}
                                alt={active.option_text || `Year ${active.year}`}
                            />
                        )}

                        {/* Title: Year only; no A/B */}
                        <h2 className="gal-modal-title">{active.year}</h2>

                        {/* Decision (option_text) */}
                        <p className="gal-modal-sub">{active.option_text}</p>

                        {/* Scenario */}
                        <p className="gal-scenario">{active.scenario}</p>
                    </div>
                </div>
            )}
        </div>
    );
}