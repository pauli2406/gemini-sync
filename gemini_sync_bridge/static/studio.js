(function () {
  function json(value) {
    return JSON.stringify(value, null, 2);
  }

  function cloneValue(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function text(id, value, isError) {
    var el = document.getElementById(id);
    if (!el) {
      return;
    }
    el.textContent = value;
    el.className = isError ? "error" : "";
  }

  function parseErrorPayload(payload) {
    if (!payload) {
      return "Request failed";
    }
    if (typeof payload === "string") {
      return payload;
    }
    if (payload.detail) {
      if (typeof payload.detail === "string") {
        return payload.detail;
      }
      return json(payload.detail);
    }
    return json(payload);
  }

  function readResponse(res) {
    var contentType = res.headers.get("content-type") || "";
    if (contentType.indexOf("application/json") !== -1) {
      return res.json().then(function (payload) {
        if (!res.ok) {
          throw new Error(parseErrorPayload(payload));
        }
        return payload;
      });
    }

    return res.text().then(function (raw) {
      if (!res.ok) {
        throw new Error(raw || "Request failed");
      }
      return raw;
    });
  }

  var catalogRoot = document.getElementById("studio-root");
  if (catalogRoot) {
    var endpoint = catalogRoot.getAttribute("data-endpoint");
    fetch(endpoint, { headers: { Accept: "application/json" }, cache: "no-store" })
      .then(readResponse)
      .then(function (payload) {
        var body = document.getElementById("studio-catalog-body");
        if (!body) {
          return;
        }
        body.textContent = "";
        (payload.items || []).forEach(function (item) {
          var row = document.createElement("tr");
          row.innerHTML =
            "<td>" +
            item.connector_id +
            "</td><td>" +
            item.mode +
            "</td><td>" +
            (item.schedule || "n/a") +
            "</td><td>" +
            String(item.schedule_enabled) +
            "</td><td>" +
            (item.last_status || "n/a") +
            "</td><td>" +
            '<a href="/studio/connectors/' +
            item.connector_id +
            '/edit">Edit</a> | <a href="/studio/connectors/' +
            item.connector_id +
            '/clone">Clone</a> | <a href="/studio/connectors/' +
            item.connector_id +
            '/pause">Pause</a> | <a href="/studio/connectors/' +
            item.connector_id +
            '/resume">Resume</a> | <a href="/studio/connectors/' +
            item.connector_id +
            '/delete">Delete</a> | <a href="/studio/connectors/' +
            item.connector_id +
            '/run">Run</a>' +
            "</td>";
          body.appendChild(row);
        });
      })
      .catch(function (err) {
        var body = document.getElementById("studio-catalog-body");
        if (body) {
          body.textContent = String(err);
        }
      });
  }

  var wizardRoot = document.getElementById("studio-wizard");
  if (!wizardRoot) {
    return;
  }

  var mode = wizardRoot.getAttribute("data-mode") || "create";
  var connectorId = wizardRoot.getAttribute("data-connector-id") || "";
  var draftEndpoint = wizardRoot.getAttribute("data-draft-endpoint") || "";
  var validateEndpoint = wizardRoot.getAttribute("data-validate-endpoint") || "";
  var previewEndpoint = wizardRoot.getAttribute("data-preview-endpoint") || "";
  var proposeEndpoint = wizardRoot.getAttribute("data-propose-endpoint") || "";
  var loadedDraft = null;

  function input(id) {
    return document.getElementById(id);
  }

  function setDraft(draft) {
    input("draft-name").value = draft.metadata.name;
    input("draft-mode").value = draft.spec.mode;
    input("draft-schedule").value = draft.schedule.cron;
    input("draft-enabled").checked = Boolean(draft.schedule.enabled);
    input("draft-source-type").value = draft.spec.source.type;
    input("draft-secret-ref").value = draft.spec.source.secretRef;
    input("draft-id-field").value = draft.spec.mapping.idField;
    input("draft-title-field").value = draft.spec.mapping.titleField;
    input("draft-content-template").value = draft.spec.mapping.contentTemplate;
    input("draft-output-bucket").value = draft.spec.output.bucket;
    input("draft-output-prefix").value = draft.spec.output.prefix;
    input("draft-project").value = draft.spec.gemini.projectId;
    input("draft-location").value = draft.spec.gemini.location;
    input("draft-datastore").value = draft.spec.gemini.dataStoreId;
  }

  function collectDraft() {
    var name = input("draft-name").value.trim();
    var modeValue = input("draft-mode").value;
    var sourceType = input("draft-source-type").value;
    var secretRef = input("draft-secret-ref").value.trim();
    var idField = input("draft-id-field").value.trim();
    var titleField = input("draft-title-field").value.trim();
    var contentTemplate = input("draft-content-template").value;
    var bucket = input("draft-output-bucket").value.trim();
    var prefix = input("draft-output-prefix").value.trim();
    var projectId = input("draft-project").value.trim();
    var location = input("draft-location").value.trim();
    var dataStoreId = input("draft-datastore").value.trim();

    var draft = loadedDraft
      ? cloneValue(loadedDraft)
      : {
          metadata: {},
          spec: {},
          schedule: {},
        };

    draft.metadata = draft.metadata || {};
    draft.spec = draft.spec || {};
    draft.spec.source = draft.spec.source || {};
    draft.spec.mapping = draft.spec.mapping || {};
    draft.spec.output = draft.spec.output || {};
    draft.spec.gemini = draft.spec.gemini || {};
    draft.spec.reconciliation = draft.spec.reconciliation || {};
    draft.schedule = draft.schedule || {};

    draft.metadata.name = name;
    draft.spec.mode = modeValue;

    draft.spec.source.type = sourceType;
    draft.spec.source.secretRef = secretRef;
    if (modeValue === "sql_pull") {
      if (!draft.spec.source.query) {
        draft.spec.source.query = "SELECT * FROM source_table WHERE updated_at > :watermark";
      }
      draft.spec.source.watermarkField = draft.spec.source.watermarkField || "updated_at";
    } else if (modeValue === "rest_pull") {
      if (!draft.spec.source.url) {
        draft.spec.source.url = "https://source.example/api/items";
      }
      draft.spec.source.method = draft.spec.source.method || "GET";
      draft.spec.source.watermarkField = draft.spec.source.watermarkField || "updated_at";
    }

    draft.spec.mapping.idField = idField;
    draft.spec.mapping.titleField = titleField;
    draft.spec.mapping.contentTemplate = contentTemplate;

    draft.spec.output.bucket = bucket;
    draft.spec.output.prefix = prefix;
    draft.spec.output.format = draft.spec.output.format || "ndjson";

    draft.spec.gemini.projectId = projectId;
    draft.spec.gemini.location = location;
    draft.spec.gemini.dataStoreId = dataStoreId;

    draft.spec.reconciliation.deletePolicy =
      draft.spec.reconciliation.deletePolicy || "auto_delete_missing";

    draft.schedule.cron = input("draft-schedule").value.trim();
    draft.schedule.enabled = input("draft-enabled").checked;

    return draft;
  }

  if (draftEndpoint) {
    fetch(draftEndpoint, { headers: { Accept: "application/json" }, cache: "no-store" })
      .then(readResponse)
      .then(function (payload) {
        if (payload.draft) {
          loadedDraft = cloneValue(payload.draft);
          if (mode === "clone") {
            loadedDraft.metadata.name = loadedDraft.metadata.name + "-copy";
          }
          setDraft(loadedDraft);
        }
      })
      .catch(function (err) {
        text("studio-output", String(err), true);
      });
  }

  var validateButton = document.getElementById("draft-validate");
  if (validateButton) {
    validateButton.addEventListener("click", function () {
      fetch(validateEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json({ draft: collectDraft() }),
      })
        .then(readResponse)
        .then(function (payload) {
          text("studio-output", json(payload), payload.valid === false);
        })
        .catch(function (err) {
          text("studio-output", String(err), true);
        });
    });
  }

  var previewButton = document.getElementById("draft-preview");
  if (previewButton) {
    previewButton.addEventListener("click", function () {
      fetch(previewEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json({ draft: collectDraft() }),
      })
        .then(readResponse)
        .then(function (payload) {
          text("studio-output", json(payload), false);
        })
        .catch(function (err) {
          text("studio-output", String(err), true);
        });
    });
  }

  var proposeButton = document.getElementById("draft-propose");
  if (proposeButton) {
    proposeButton.addEventListener("click", function () {
      var action = mode;
      if (!["create", "edit", "clone", "delete", "pause", "resume"].includes(action)) {
        action = "create";
      }
      var payload = {
        action: action,
        connector_id: connectorId || collectDraft().metadata.name,
      };
      if (["create", "edit", "clone"].includes(action)) {
        payload.draft = collectDraft();
      }

      fetch(proposeEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json(payload),
      })
        .then(readResponse)
        .then(function (responsePayload) {
          text("studio-output", json(responsePayload), false);
        })
        .catch(function (err) {
          text("studio-output", String(err), true);
        });
    });
  }

  if (mode === "run") {
    fetch("/v1/studio/connectors/" + connectorId + "/run-now", { method: "POST" })
      .then(readResponse)
      .then(function (payload) {
        text("studio-output", json(payload), false);
      })
      .catch(function (err) {
        text("studio-output", String(err), true);
      });
  }
})();
