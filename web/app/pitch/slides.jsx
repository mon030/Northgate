"use client";
import { useEffect, useRef, useState } from "react";
import "reveal.js/reveal.css";
import "./slides.css";
import slides from "./slides.json";
export default function Deck() {
  const node = useRef(null),
    api = useRef(null);
  const [index, setIndex] = useState(0);
  useEffect(() => {
    let cancelled = false;
    let engine;
    import("reveal.js").then(async ({ default: Reveal }) => {
      if (cancelled) return;
      engine = new Reveal(node.current, {
        embedded: true,
        width: 1000,
        height: 535,
        margin: 0.06,
        controls: false,
        progress: false,
        transition: "none",
        keyboardCondition: "focused",
        center: true,
      });
      await engine.initialize();
      if (cancelled) {
        engine.destroy();
        return;
      }
      api.current = engine;
      engine.on("slidechanged", (e) => setIndex(e.indexh));
    });
    return () => {
      cancelled = true;
      if (api.current) {
        api.current.destroy();
        api.current = null;
      }
    };
  }, []);
  return (
    <section className="panel">
      <div className="pitch-frame">
        <div className="reveal" ref={node} tabIndex={0}>
          <div className="slides">
            {slides.map((s) => (
              <section key={s.title}>
                <p className="slide-owner">{s.owner}</p>
                <h2>{s.title}</h2>
                <strong>{s.value}</strong>
                <p>{s.text}</p>
                {s.link && (
                  <a
                    className="textlink"
                    href={s.link}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {s.label}
                  </a>
                )}
              </section>
            ))}
          </div>
        </div>
      </div>
      <div className="section-head">
        <button
          className="btn"
          disabled={!index}
          onClick={() => api.current?.prev()}
        >
          Previous
        </button>
        <span>
          Slide {index + 1} of {slides.length}
        </span>
        <button
          className="btn btn-primary"
          disabled={index === slides.length - 1}
          onClick={() => api.current?.next()}
        >
          Next slide
        </button>
      </div>
    </section>
  );
}
