(() => {
  "use strict";

  const params = new URLSearchParams(window.location.search);
  const token = params.get("token") || "";
  const state = {
    ledger: null,
    draggingId: null,
    poll: null,
    saving: false,
    editing: null,
    snackbarAction: null,
    snackbarTimer: null,
    snackbarRemaining: 0,
    snackbarStartedAt: 0,
  };

  const elements = {
    title: document.querySelector("#ledger-title"),
    openCount: document.querySelector("#open-count"),
    doneCount: document.querySelector("#done-count"),
    transferredCount: document.querySelector("#transferred-count"),
    updated: document.querySelector("#updated-label"),
    openList: document.querySelector("#open-list"),
    doneList: document.querySelector("#done-list"),
    transferredList: document.querySelector("#transferred-list"),
    openEmpty: document.querySelector("#open-empty"),
    doneEmpty: document.querySelector("#done-empty"),
    transferredEmpty: document.querySelector("#transferred-empty"),
    saveState: document.querySelector("#save-state"),
    saveLabel: document.querySelector("#save-label"),
    ledgerPath: document.querySelector("#ledger-path"),
    template: document.querySelector("#item-template"),
    snackbar: document.querySelector("#snackbar"),
    snackbarMessage: document.querySelector("#snackbar-message"),
    snackbarAction: document.querySelector("#snackbar-action"),
    liveStatus: document.querySelector("#live-status"),
  };
  elements.transferredSection = elements.transferredList.closest(".ledger-section");

  // Plain-language tooltip copy. An item's own `explanation` is preferred; these
  // sentences are the fallback for a ledger written before that field existed.
  const TOOLTIP_LABELS = {
    requested: "On your list",
    planned: "Approach agreed",
    "in-progress": "Picked up",
    implemented: "Change made",
    verified: "Checked and finished",
    "waiting-on-you": "Waiting on you",
    blocked: "Held up elsewhere",
    reminder: "Parked on purpose",
    dropped: "Not doing this one",
  };

  const TOOLTIP_TEXT = {
    requested:
      "This one is here because you asked for it. Nothing has started, and it will wait quietly until you decide it is the right moment.",
    planned:
      "There is an agreed way to do this one, and nothing has changed yet. It is ready for you whenever it suits.",
    "in-progress":
      "You asked for this one to be picked up, so work went into it then. It sits here until you say what happens with it next.",
    implemented:
      "The change for this one has been made, and it has not been checked yet. A quick check is the natural next step whenever you want it.",
    verified:
      "This one is finished and was checked, so you can happily leave it behind. It stays on the list as a record of what happened.",
    "waiting-on-you":
      "This one is ready and just needs a moment from you — a click, a yes, a key, or a choice. Nothing else is holding it up.",
    blocked:
      "Something outside this list is in the way for now, so this one is parked rather than forgotten. It can move again once that clears.",
    reminder:
      "You parked this one on purpose. It stays visible for whenever you want it, and nothing will start it for you.",
    dropped:
      "You decided against this one. It stays here so the reasoning is easy to find later.",
  };

  const TOOLTIP_FALLBACK =
    "This one is on your list, and it stays here until you decide what happens with it.";

  const PROVENANCE = {
    "user-requested": {
      label: "You",
      description: "You asked for this item.",
    },
    "agent-added": {
      label: "Agent",
      description: "An agent added this item because it was genuinely useful to track.",
    },
  };

  function apiUrl(path) {
    const query = new URLSearchParams({ token });
    return `${path}?${query.toString()}`;
  }

  function setSaveState(kind, label) {
    elements.saveState.dataset.state = kind;
    elements.saveLabel.textContent = label;
  }

  function announce(message) {
    elements.liveStatus.textContent = "";
    window.requestAnimationFrame(() => { elements.liveStatus.textContent = message; });
  }

  function hideSnackbar() {
    window.clearTimeout(state.snackbarTimer);
    state.snackbarTimer = null;
    state.snackbarAction = null;
    state.snackbarRemaining = 0;
    elements.snackbar.hidden = true;
    elements.snackbarAction.hidden = true;
  }

  function startSnackbarTimer(delay) {
    window.clearTimeout(state.snackbarTimer);
    state.snackbarRemaining = delay;
    state.snackbarStartedAt = Date.now();
    state.snackbarTimer = window.setTimeout(hideSnackbar, delay);
  }

  function pauseSnackbarTimer() {
    if (!state.snackbarTimer) return;
    window.clearTimeout(state.snackbarTimer);
    state.snackbarTimer = null;
    state.snackbarRemaining = Math.max(0, state.snackbarRemaining - (Date.now() - state.snackbarStartedAt));
  }

  function resumeSnackbarTimer() {
    if (!elements.snackbar.hidden && !state.snackbarTimer && state.snackbarRemaining > 0) {
      startSnackbarTimer(state.snackbarRemaining);
    }
  }

  function showSnackbar(message, action = null) {
    window.clearTimeout(state.snackbarTimer);
    elements.snackbarMessage.textContent = message;
    elements.snackbar.hidden = false;
    state.snackbarAction = action;
    elements.snackbarAction.hidden = !action;
    elements.snackbarAction.textContent = action?.label || "Undo";
    startSnackbarTimer(action ? 8000 : 4200);
  }

  async function request(path, options = {}) {
    const response = await fetch(apiUrl(path), {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Ledger-Token": token,
        ...(options.headers || {}),
      },
      cache: "no-store",
    });
    const payload = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
    if (!response.ok) {
      const error = new Error(payload.error || `HTTP ${response.status}`);
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return payload;
  }

  function orderedItems(completed) {
    return state.ledger.items
      .filter((item) => item.completed === completed && item.tracking_state !== "transferred")
      .sort((a, b) => a.position - b.position || a.id.localeCompare(b.id));
  }

  function transferredItems() {
    return state.ledger.items
      .filter((item) => item.tracking_state === "transferred")
      .sort((a, b) => {
        const timeOrder = (b.transferred_to?.transferred_at || "").localeCompare(
          a.transferred_to?.transferred_at || "",
        );
        return timeOrder || a.id.localeCompare(b.id, undefined, { numeric: true });
      });
  }

  function formatUpdated(value) {
    if (!value) return "Update time unavailable";
    const date = new Date(value);
    return Number.isNaN(date.valueOf()) ? `Updated ${value}` : `Updated ${date.toLocaleString()}`;
  }

  function autoSizeEditor(editor) {
    editor.style.height = "auto";
    editor.style.height = `${editor.scrollHeight}px`;
  }

  function tooltipLabel(item, transferred) {
    if (transferred) return `${item.id} · Looked after elsewhere`;
    return `${item.id} · ${TOOLTIP_LABELS[item.status] || "On your list"}`;
  }

  function tooltipText(item, transferred) {
    const written = typeof item.explanation === "string" ? item.explanation.trim() : "";
    if (written) return written;
    if (transferred) {
      const destination = (item.transferred_to?.title || "").trim() || "Another task";
      return `${destination} looks after this one now. It stays here as a record, with its wording and status kept exactly as they were.`;
    }
    return TOOLTIP_TEXT[item.status] || TOOLTIP_FALLBACK;
  }

  function attachTooltip(node, item, transferred) {
    const tooltip = node.querySelector(".item-tooltip");
    if (!tooltip) return;
    tooltip.id = `item-tooltip-${item.id}`;
    tooltip.querySelector(".item-tooltip-label").textContent = tooltipLabel(item, transferred);
    tooltip.querySelector(".item-tooltip-text").textContent = tooltipText(item, transferred);
    node.querySelector(".item-title")?.setAttribute("aria-describedby", tooltip.id);
    node.dataset.tooltip = "above";

    // Prefer showing it above the row, and flip below only when the row sits too
    // close to the top of the viewport for the tooltip to fit.
    const place = () => {
      node.classList.remove("tooltip-dismissed");
      const room = node.getBoundingClientRect().top;
      node.dataset.tooltip = room < tooltip.offsetHeight + 16 ? "below" : "above";
    };
    const restore = () => node.classList.remove("tooltip-dismissed");
    node.addEventListener("pointerenter", place);
    node.addEventListener("focusin", place);
    node.addEventListener("pointerleave", restore);
    node.addEventListener("focusout", restore);
    node.addEventListener("keydown", (event) => {
      // Dismissible without moving the pointer or the focus.
      if (event.key !== "Escape" || state.editing?.id === item.id) return;
      node.classList.add("tooltip-dismissed");
    });
  }

  function attachProvenance(node, item) {
    const badge = node.querySelector(".provenance-badge");
    const provenance = PROVENANCE[item.provenance];
    if (!provenance) {
      delete node.dataset.provenanceDescription;
      badge.hidden = true;
      badge.textContent = "";
      badge.removeAttribute("data-provenance");
      badge.removeAttribute("data-tooltip");
      badge.removeAttribute("aria-label");
      return;
    }
    badge.hidden = false;
    node.dataset.provenanceDescription = provenance.description;
    badge.textContent = provenance.label;
    badge.dataset.provenance = item.provenance;
    badge.dataset.tooltip = provenance.description;
    badge.setAttribute("aria-label", `Provenance: ${provenance.description}`);
    badge.addEventListener("pointerenter", () => node.classList.add("provenance-hovered"));
    badge.addEventListener("pointerleave", () => node.classList.remove("provenance-hovered"));
  }

  function beginEdit(node, item, initialValue = item.title) {
    if (item.tracking_state === "transferred") return;
    if (state.editing && state.editing.id !== item.id) state.editing.cancel();
    if (state.editing?.id === item.id) return;

    const titleButton = node.querySelector(".item-title");
    if (!titleButton) return;
    const editor = document.createElement("textarea");
    editor.className = "edit-input";
    editor.maxLength = 500;
    editor.rows = 1;
    editor.value = initialValue;
    editor.setAttribute("aria-label", `Edit ${item.id}`);
    titleButton.replaceWith(editor);
    autoSizeEditor(editor);

    let finished = false;
    const cancel = () => {
      if (finished) return;
      finished = true;
      editor.replaceWith(titleButton);
      state.editing = null;
      titleButton.focus();
    };

    const commit = async () => {
      if (finished) return;
      const nextTitle = editor.value.trim();
      if (!nextTitle) {
        showSnackbar("Empty task not saved.");
        cancel();
        return;
      }
      if (nextTitle === item.title) {
        cancel();
        return;
      }

      editor.disabled = true;
      editor.setAttribute("aria-busy", "true");
      const draft = editor.value;
      finished = true;
      state.editing = null;
      const result = await saveMutation({ action: "edit", id: item.id, title: nextTitle });
      if (!result.ok) {
        if (result.error?.status === 409) {
          window.setTimeout(() => reopenEditor(item.id, draft), 0);
        } else if (editor.isConnected) {
          finished = false;
          editor.disabled = false;
          editor.removeAttribute("aria-busy");
          state.editing = { id: item.id, cancel, commit, draft: () => editor.value };
          editor.focus();
        }
      }
    };

    state.editing = { id: item.id, cancel, commit, draft: () => editor.value };
    editor.addEventListener("input", () => autoSizeEditor(editor));
    editor.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        cancel();
      } else if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        commit();
      }
    });
    editor.addEventListener("blur", () => commit());
    editor.focus();
    editor.select();
  }

  function reopenEditor(id, draft) {
    const row = [...document.querySelectorAll(".ledger-item")].find((candidate) => candidate.dataset.id === id);
    const item = state.ledger?.items.find((candidate) => candidate.id === id);
    if (row && item && item.tracking_state !== "transferred") beginEdit(row, item, draft);
  }

  function createItem(item, completed, transferred = false) {
    const node = elements.template.content.firstElementChild.cloneNode(true);
    node.dataset.id = item.id;
    node.dataset.status = item.status;
    node.classList.toggle("transferred", transferred);
    attachProvenance(node, item);

    const checkbox = node.querySelector(".item-check");
    checkbox.checked = completed;
    checkbox.disabled = transferred;
    checkbox.setAttribute("aria-label", `${completed ? "Reopen" : "Complete"} ${item.id}: ${item.title}`);
    if (!transferred) {
      checkbox.addEventListener("change", async () => {
        const nextCompleted = checkbox.checked;
        const result = await saveMutation({ action: "toggle", id: item.id, completed: nextCompleted });
        if (!result.ok) {
          checkbox.checked = !nextCompleted;
          return;
        }
        if (nextCompleted) {
          const shortTitle = item.title.length > 72 ? `${item.title.slice(0, 69)}…` : item.title;
          showSnackbar(`Completed “${shortTitle}”`, {
            label: "Undo",
            run: () => undoCompletion(item.id),
          });
        }
      });
    } else {
      node.querySelector(".check-wrap").hidden = true;
    }

    const title = node.querySelector(".item-title");
    node.querySelector(".item-title-text").textContent = item.title;
    if (transferred) {
      const readOnlyTitle = document.createElement("span");
      readOnlyTitle.className = "item-title item-title--readonly";
      const readOnlyText = document.createElement("span");
      readOnlyText.className = "item-title-text";
      readOnlyText.textContent = item.title;
      const badge = node.querySelector(".provenance-badge");
      readOnlyTitle.append(readOnlyText, badge);
      readOnlyTitle.setAttribute(
        "aria-label",
        `${item.title}. ${item.id}. ${item.status}. ${node.dataset.provenanceDescription || "Source not recorded."} Owned by ${item.transferred_to?.title || "another task"}; read-only here.`,
      );
      title.replaceWith(readOnlyTitle);
    } else {
      title.setAttribute(
        "aria-label",
        `${item.title}. ${item.id}. Status ${item.status}. ${node.dataset.provenanceDescription || "Source not recorded."} Click to edit.`,
      );
      title.addEventListener("click", () => beginEdit(node, item));
      title.addEventListener("keydown", (event) => {
        if (!event.altKey || !["ArrowUp", "ArrowDown"].includes(event.key) || completed) return;
        event.preventDefault();
        moveBy(item.id, event.key === "ArrowUp" ? -1 : 1);
      });
    }

    attachTooltip(node, item, transferred);

    const dragHandle = node.querySelector(".drag-handle");
    dragHandle.hidden = completed || transferred;
    dragHandle.setAttribute("aria-label", `Drag ${item.id} to reorder`);
    dragHandle.addEventListener("dragstart", (event) => {
      state.draggingId = item.id;
      node.classList.add("dragging");
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", item.id);
    });
    dragHandle.addEventListener("dragend", () => {
      state.draggingId = null;
      node.classList.remove("dragging");
      document.querySelectorAll(".drag-over").forEach((row) => row.classList.remove("drag-over"));
    });
    node.addEventListener("dragover", (event) => {
      if (completed || transferred || !state.draggingId || state.draggingId === item.id) return;
      event.preventDefault();
      node.classList.add("drag-over");
    });
    node.addEventListener("dragleave", () => node.classList.remove("drag-over"));
    node.addEventListener("drop", (event) => {
      if (completed || transferred || !state.draggingId || state.draggingId === item.id) return;
      event.preventDefault();
      node.classList.remove("drag-over");
      reorderRelative(state.draggingId, item.id);
    });

    const up = node.querySelector(".move-up");
    const down = node.querySelector(".move-down");
    up.hidden = completed || transferred;
    down.hidden = completed || transferred;
    up.addEventListener("click", () => moveBy(item.id, -1));
    down.addEventListener("click", () => moveBy(item.id, 1));
    node.querySelector(".item-actions").hidden = completed || transferred;
    return node;
  }

  function render({ preserveEdit = false, focusId = null } = {}) {
    if (!state.ledger) return;
    const editSnapshot = preserveEdit && state.editing
      ? { id: state.editing.id, draft: state.editing.draft() }
      : null;
    state.editing = null;

    const open = orderedItems(false);
    const done = orderedItems(true);
    const transferred = transferredItems();
    elements.title.textContent = state.ledger.title;
    document.title = `${state.ledger.title} — Outstanding Items`;
    elements.openCount.textContent = String(open.length);
    elements.doneCount.textContent = String(done.length);
    elements.transferredCount.textContent = String(transferred.length);
    elements.updated.textContent = `${formatUpdated(state.ledger.updated_at)} · revision ${state.ledger.revision}`;
    elements.ledgerPath.textContent = state.ledger._runtime?.ledger_path || "Canonical JSON ledger";
    elements.ledgerPath.title = elements.ledgerPath.textContent;
    elements.openList.replaceChildren(...open.map((item) => createItem(item, false)));
    elements.doneList.replaceChildren(...done.map((item) => createItem(item, true)));
    elements.transferredList.replaceChildren(
      ...transferred.map((item) => createItem(item, item.completed, true)),
    );
    elements.openEmpty.hidden = open.length !== 0;
    elements.doneEmpty.hidden = done.length !== 0;
    elements.transferredEmpty.hidden = transferred.length !== 0;
    elements.transferredSection.hidden = transferred.length === 0;
    [...elements.openList.children].forEach((row, index, rows) => {
      row.querySelector(".move-up").disabled = index === 0;
      row.querySelector(".move-down").disabled = index === rows.length - 1;
    });
    if (editSnapshot) {
      window.setTimeout(() => reopenEditor(editSnapshot.id, editSnapshot.draft), 0);
    } else if (focusId) {
      window.setTimeout(() => {
        const row = [...elements.openList.children].find((candidate) => candidate.dataset.id === focusId);
        row?.querySelector(".item-title")?.focus();
      }, 0);
    }
  }

  function moveBy(id, delta) {
    const order = orderedItems(false).map((item) => item.id);
    const index = order.indexOf(id);
    const next = index + delta;
    if (index < 0 || next < 0 || next >= order.length) return;
    [order[index], order[next]] = [order[next], order[index]];
    saveMutation({ action: "reorder", order }, { focusId: id }).then((result) => {
      if (result.ok) announce(`Moved ${id} to position ${next + 1} of ${order.length}.`);
    });
  }

  function reorderRelative(sourceId, targetId) {
    const order = orderedItems(false).map((item) => item.id).filter((id) => id !== sourceId);
    const targetIndex = order.indexOf(targetId);
    if (targetIndex < 0) return;
    order.splice(targetIndex, 0, sourceId);
    saveMutation({ action: "reorder", order }).then((result) => {
      if (result.ok) announce(`Moved ${sourceId} to position ${targetIndex + 1} of ${order.length}.`);
    });
  }

  async function undoCompletion(id) {
    const current = state.ledger?.items.find((item) => item.id === id);
    if (!current?.completed || current.tracking_state === "transferred") {
      showSnackbar("That task is already open.");
      return;
    }
    hideSnackbar();
    const result = await saveMutation({ action: "toggle", id, completed: false });
    if (result.ok) showSnackbar("Moved back to open items.");
  }

  async function saveMutation(change, { focusId = null } = {}) {
    if (state.saving) {
      const error = new Error("Another change is still saving.");
      showSnackbar(error.message);
      return { ok: false, error };
    }
    state.saving = true;
    setSaveState("saving", "Saving…");
    try {
      state.ledger = await request("/api/mutate", {
        method: "POST",
        body: JSON.stringify({ ...change, base_revision: state.ledger.revision }),
      });
      render({ focusId });
      setSaveState("saved", "Saved");
      return { ok: true };
    } catch (error) {
      if (error.status === 409 && error.payload?.ledger) {
        state.ledger = error.payload.ledger;
        render();
      }
      setSaveState("error", "Save failed");
      showSnackbar(error.message || "The ledger could not be saved.");
      return { ok: false, error };
    } finally {
      state.saving = false;
    }
  }

  async function refresh(silent = false) {
    if (!token) {
      setSaveState("error", "Missing access token");
      showSnackbar("Open the Full outstanding items link supplied by the agent; it contains the local access token.");
      return;
    }
    if (!silent) setSaveState("saving", "Loading…");
    try {
      const ledger = await request("/api/ledger");
      if (!state.ledger || ledger.revision !== state.ledger.revision) {
        state.ledger = ledger;
        render({ preserveEdit: true });
      }
      setSaveState("saved", "Saved");
    } catch (error) {
      setSaveState("error", "Disconnected");
      if (!silent) showSnackbar(error.message || "Could not load the ledger.");
    }
  }

  elements.snackbarAction.addEventListener("click", async () => {
    const action = state.snackbarAction;
    if (!action) return;
    elements.snackbarAction.disabled = true;
    try {
      await action.run();
    } finally {
      elements.snackbarAction.disabled = false;
    }
  });
  elements.snackbar.addEventListener("mouseenter", pauseSnackbarTimer);
  elements.snackbar.addEventListener("mouseleave", resumeSnackbarTimer);
  elements.snackbar.addEventListener("focusin", pauseSnackbarTimer);
  elements.snackbar.addEventListener("focusout", resumeSnackbarTimer);
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z" && state.snackbarAction) {
      event.preventDefault();
      elements.snackbarAction.click();
    }
  });

  refresh();
  state.poll = window.setInterval(() => {
    if (!state.saving && document.visibilityState === "visible") refresh(true);
  }, 2000);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && !state.saving) refresh(true);
  });
})();
