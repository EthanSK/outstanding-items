/* Outstanding Items — progressive enhancement only.
 *
 * The page is complete and readable without this file: the markup already
 * contains the final state of the ledger and the whole transcript. All this
 * does is rewind the story and let you play it forward.
 *
 * No dependencies, no network, no storage.
 */
(function () {
  "use strict";

  var MARKS = {
    requested: "·",
    planned: "–",
    "in-progress": "→",
    implemented: "▪",
    verified: "✓",
    "waiting-on-you": "»",
    blocked: "!",
    reminder: "◦",
    dropped: "×"
  };

  var STEP_MS = 3400;

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined && text !== null) {
      node.textContent = text;
    }
    return node;
  }

  function prefersReducedMotion() {
    return (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function parseData() {
    var script = document.getElementById("ledger-data");
    if (!script) {
      return null;
    }
    try {
      var data = JSON.parse(script.textContent);
      if (!data || !Array.isArray(data.steps) || data.steps.length === 0) {
        return null;
      }
      return data;
    } catch (err) {
      return null;
    }
  }

  function itemRow(item, touched) {
    var li = el("li");
    li.setAttribute("data-status", item.status);
    if (touched) {
      li.className = "is-touched";
    }

    var mark = el("span", "mark", MARKS[item.status] || "·");
    mark.setAttribute("aria-hidden", "true");
    li.appendChild(mark);

    var row = el("span", "row");
    row.appendChild(el("span", "oi", item.id));
    row.appendChild(el("span", "title", item.title));
    row.appendChild(document.createTextNode(" "));
    row.appendChild(el("span", "status", item.status));
    if (item.qual) {
      row.appendChild(document.createTextNode(" "));
      row.appendChild(el("span", "qual", "(" + item.qual + ")"));
    }
    li.appendChild(row);
    return li;
  }

  function renderLedger(target, step, animate) {
    var touched = step.touched || [];
    var frag = document.createDocumentFragment();

    var head = el("p", "ledger-head");
    head.appendChild(el("strong", null, "Outstanding"));
    head.appendChild(document.createTextNode(" "));
    var forUser = step.open.filter(function (item) {
      return item.status !== "waiting-on-you" && item.status !== "reminder";
    });
    var waiting = step.open.filter(function (item) {
      return item.status === "waiting-on-you";
    });
    var reminders = step.open.filter(function (item) {
      return item.status === "reminder";
    });
    var counts = [];
    if (forUser.length) counts.push(forUser.length + " for you");
    if (waiting.length) counts.push(waiting.length + " waiting on you");
    if (reminders.length) counts.push(reminders.length + (reminders.length === 1 ? " reminder" : " reminders"));
    if (step.done.length) counts.push(step.done.length + " done");
    head.appendChild(el("span", "ledger-count", counts.join(" · ")));
    frag.appendChild(head);

    function appendSection(label, items) {
      if (!items.length) return;
      var subhead = el("p", "ledger-subhead");
      subhead.appendChild(el("strong", null, label));
      frag.appendChild(subhead);
      var list = el("ul", "ledger-list");
      items.forEach(function (item) {
        list.appendChild(itemRow(item, touched.indexOf(item.id) !== -1));
      });
      frag.appendChild(list);
    }

    appendSection("Outstanding for you", forUser);
    appendSection("Waiting on you", waiting);
    appendSection("Intentional reminders", reminders);

    /* The recommendation is deliberately absent on most turns. */
    if (step.next) {
      var next = el("p", "ledger-next");
      next.appendChild(el("strong", null, "Suggested for you"));
      next.appendChild(document.createTextNode(" — "));
      next.appendChild(el("span", "next-id", step.next.id));
      next.appendChild(document.createTextNode(" "));
      next.appendChild(el("span", "next-step", step.next.step));
      frag.appendChild(next);
      if (step.next.why) {
        frag.appendChild(el("p", "ledger-why", step.next.why));
      }
    }

    if (step.related && step.related.length) {
      step.related.forEach(function (rel) {
        frag.appendChild(
          el(
            "p",
            "ledger-related",
            "Related: " + rel.title + " · " + rel.id + " — " + rel.result
          )
        );
      });
    }

    if (step.done.length) {
      var subhead = el("p", "ledger-subhead");
      subhead.appendChild(el("strong", null, "Done"));
      frag.appendChild(subhead);

      var doneList = el("ul", "ledger-list is-done");
      step.done.forEach(function (item) {
        doneList.appendChild(itemRow(item, touched.indexOf(item.id) !== -1));
      });
      frag.appendChild(doneList);
    }

    target.textContent = "";
    target.appendChild(frag);

    if (animate) {
      target.classList.remove("is-new");
      /* Reading offsetWidth restarts the animation without a timer. */
      void target.offsetWidth;
      target.classList.add("is-new");
    }
  }

  function init() {
    var data = parseData();
    var body = document.getElementById("ledger-body");
    var stream = document.getElementById("stream-list");
    var controls = document.getElementById("demo-controls");
    var toggle = document.getElementById("demo-toggle");
    var stepBtn = document.getElementById("demo-step");
    var restartBtn = document.getElementById("demo-restart");
    var status = document.getElementById("demo-status");
    var caption = document.getElementById("demo-caption");

    if (!data || !body || !stream || !controls || !toggle || !stepBtn || !restartBtn || !status || !caption) {
      return; /* Leave the static page exactly as authored. */
    }

    var lines = Array.prototype.slice.call(stream.children);
    var steps = data.steps;
    if (lines.length !== steps.length) {
      return; /* Markup and data disagree; do not touch anything. */
    }

    var index = 0;
    var timer = null;
    var playing = false;
    var finished = false;

    function show(i, animate) {
      index = i;
      var step = steps[i];

      lines.forEach(function (line, n) {
        line.hidden = n > i;
        if (n === i && animate) {
          line.classList.remove("is-new");
          void line.offsetWidth;
          line.classList.add("is-new");
        } else if (n !== i) {
          line.classList.remove("is-new");
        }
      });

      renderLedger(body, step, animate);
      caption.textContent = step.note || "";
      status.textContent = "Turn " + (i + 1) + " of " + steps.length;
      finished = i >= steps.length - 1;
      if (finished) {
        stop();
        toggle.textContent = "Replay";
      }
    }

    function tick() {
      if (index >= steps.length - 1) {
        stop();
        return;
      }
      show(index + 1, true);
    }

    function play() {
      if (playing) {
        return;
      }
      if (finished) {
        show(0, true);
      }
      playing = true;
      toggle.textContent = "Pause";
      timer = window.setInterval(tick, STEP_MS);
    }

    function stop() {
      playing = false;
      if (timer !== null) {
        window.clearInterval(timer);
        timer = null;
      }
      toggle.textContent = finished ? "Replay" : "Play";
    }

    toggle.addEventListener("click", function () {
      if (playing) {
        stop();
      } else {
        play();
      }
    });

    stepBtn.addEventListener("click", function () {
      stop();
      show(index >= steps.length - 1 ? 0 : index + 1, true);
    });

    restartBtn.addEventListener("click", function () {
      stop();
      finished = false;
      show(0, true);
    });

    document.addEventListener("visibilitychange", function () {
      if (document.hidden && playing) {
        stop();
      }
    });

    controls.hidden = false;
    show(0, false);
    stop();

    if (prefersReducedMotion()) {
      /* Static by default. The controls are still there if you want them. */
      return;
    }

    if (typeof window.IntersectionObserver === "function") {
      var observer = new window.IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              observer.disconnect();
              play();
            }
          });
        },
        { threshold: 0.25 }
      );
      observer.observe(body);
    } else {
      play();
    }
  }

  function initCopyButtons() {
    if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
      return;
    }
    var blocks = document.querySelectorAll(".codeblock");
    Array.prototype.forEach.call(blocks, function (block) {
      var button = block.querySelector(".copy");
      var code = block.querySelector("code");
      if (!button || !code) {
        return;
      }
      button.hidden = false;
      button.addEventListener("click", function () {
        navigator.clipboard.writeText(code.textContent).then(
          function () {
            var previous = button.textContent;
            button.textContent = "Copied";
            window.setTimeout(function () {
              button.textContent = previous;
            }, 1600);
          },
          function () {
            button.textContent = "Press ⌘C";
          }
        );
      });
    });
  }

  function boot() {
    init();
    initCopyButtons();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
