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
  var DEFAULT_SQL_QUERY = "SELECT * FROM source_table WHERE updated_at > :watermark";
  var DEFAULT_REST_URL = "https://source.example/api/items";
  var DEFAULT_WATERMARK_FIELD = "updated_at";
  var DEFAULT_REST_AUTH_MODE = "static_bearer";
  var DEFAULT_OAUTH_TOKEN_URL =
    "https://auth.example/realms/acme/protocol/openid-connect/token";
  var DEFAULT_OAUTH_CLIENT_AUTH_METHOD = "client_secret_post";
  var SQL_SOURCE_TYPES = ["postgres", "mssql", "mysql", "oracle"];
  var REST_SOURCE_TYPES = ["http"];

  function input(id) {
    return document.getElementById(id);
  }

  function valueOrEmpty(value) {
    if (value === null || typeof value === "undefined") {
      return "";
    }
    return String(value);
  }

  function setSelectOptions(selectId, values, preferredValue) {
    var select = input(selectId);
    if (!select) {
      return;
    }

    var selected = preferredValue || select.value;
    select.textContent = "";
    values.forEach(function (value) {
      var option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });

    if (values.indexOf(selected) !== -1) {
      select.value = selected;
      return;
    }
    select.value = values[0] || "";
  }

  function parseJsonField(id, fieldName, fallback) {
    var raw = input(id).value.trim();
    if (!raw) {
      return fallback;
    }
    try {
      return JSON.parse(raw);
    } catch (_err) {
      throw new Error(fieldName + " must be valid JSON");
    }
  }

  function parseMetadataFields(raw) {
    if (!raw.trim()) {
      return [];
    }
    return raw
      .split(",")
      .map(function (item) {
        return item.trim();
      })
      .filter(Boolean);
  }

  function parseScopes(raw) {
    if (!raw.trim()) {
      return [];
    }
    return raw
      .split(",")
      .map(function (item) {
        return item.trim();
      })
      .filter(Boolean);
  }

  function refreshModeVisibility(modeValue) {
    var elements = wizardRoot.querySelectorAll("[data-visible-modes]");
    elements.forEach(function (el) {
      var modes = (el.getAttribute("data-visible-modes") || "")
        .split(/\s+/)
        .filter(Boolean);
      el.hidden = modes.indexOf(modeValue) === -1;
    });
  }

  function refreshAuthModeVisibility(modeValue, authModeValue) {
    var elements = wizardRoot.querySelectorAll("[data-visible-auth-modes]");
    elements.forEach(function (el) {
      if (modeValue !== "rest_pull") {
        el.hidden = true;
        return;
      }
      var authModes = (el.getAttribute("data-visible-auth-modes") || "")
        .split(/\s+/)
        .filter(Boolean);
      el.hidden = authModes.indexOf(authModeValue) === -1;
    });
  }

  function applyModeSourceType(modeValue) {
    if (modeValue === "sql_pull") {
      setSelectOptions("draft-source-type", SQL_SOURCE_TYPES, input("draft-source-type").value);
      return;
    }
    setSelectOptions("draft-source-type", REST_SOURCE_TYPES, "http");
  }

  function applyFieldDefaults(modeValue) {
    if (modeValue === "sql_pull" && !input("draft-source-query").value.trim()) {
      input("draft-source-query").value = DEFAULT_SQL_QUERY;
    }
    if (modeValue === "rest_pull" && !input("draft-source-url").value.trim()) {
      input("draft-source-url").value = DEFAULT_REST_URL;
    }
    if (
      (modeValue === "sql_pull" || modeValue === "rest_pull") &&
      !input("draft-source-watermark").value.trim()
    ) {
      input("draft-source-watermark").value = DEFAULT_WATERMARK_FIELD;
    }
    if (!input("draft-mime-type").value.trim()) {
      input("draft-mime-type").value = "text/plain";
    }
    if (!input("draft-output-format").value.trim()) {
      input("draft-output-format").value = "ndjson";
    }
    if (modeValue === "rest_pull" && !input("draft-source-auth-mode").value) {
      input("draft-source-auth-mode").value = DEFAULT_REST_AUTH_MODE;
    }
    if (
      modeValue === "rest_pull" &&
      input("draft-source-auth-mode").value === "oauth_client_credentials" &&
      !input("draft-source-oauth-token-url").value.trim()
    ) {
      input("draft-source-oauth-token-url").value = DEFAULT_OAUTH_TOKEN_URL;
    }
    if (
      modeValue === "rest_pull" &&
      input("draft-source-auth-mode").value === "oauth_client_credentials" &&
      !input("draft-source-oauth-client-auth-method").value
    ) {
      input("draft-source-oauth-client-auth-method").value = DEFAULT_OAUTH_CLIENT_AUTH_METHOD;
    }
  }

  function refreshModeState(modeValue, authModeOverride) {
    refreshModeVisibility(modeValue);
    applyModeSourceType(modeValue);
    if (modeValue !== "rest_pull") {
      refreshAuthModeVisibility(modeValue, DEFAULT_REST_AUTH_MODE);
      applyFieldDefaults(modeValue);
      return;
    }

    var authMode = authModeOverride || input("draft-source-auth-mode").value || DEFAULT_REST_AUTH_MODE;
    input("draft-source-auth-mode").value = authMode;
    refreshAuthModeVisibility(modeValue, authMode);
    applyFieldDefaults(modeValue);
  }

  function setDraft(draft) {
    var source = draft.spec.source || {};
    var mapping = draft.spec.mapping || {};
    var output = draft.spec.output || {};
    var gemini = draft.spec.gemini || {};
    var reconciliation = draft.spec.reconciliation || {};

    input("draft-name").value = valueOrEmpty(draft.metadata.name);
    input("draft-mode").value = valueOrEmpty(draft.spec.mode);
    input("draft-schedule").value = valueOrEmpty(draft.schedule.cron);
    input("draft-enabled").checked = Boolean(draft.schedule.enabled);

    var authMode = source.oauth ? "oauth_client_credentials" : DEFAULT_REST_AUTH_MODE;
    input("draft-source-auth-mode").value = authMode;
    refreshModeState(draft.spec.mode, authMode);
    setSelectOptions(
      "draft-source-type",
      draft.spec.mode === "sql_pull" ? SQL_SOURCE_TYPES : REST_SOURCE_TYPES,
      source.type
    );
    input("draft-secret-ref").value = valueOrEmpty(source.secretRef);
    input("draft-source-query").value = valueOrEmpty(source.query || DEFAULT_SQL_QUERY);
    input("draft-source-url").value = valueOrEmpty(source.url || DEFAULT_REST_URL);
    input("draft-source-method").value = valueOrEmpty(source.method || "GET");
    input("draft-source-watermark").value = valueOrEmpty(
      source.watermarkField || DEFAULT_WATERMARK_FIELD
    );
    input("draft-source-payload").value = json(source.payload || {});
    input("draft-source-pagination-cursor").value = valueOrEmpty(source.paginationCursorField);
    input("draft-source-pagination-next").value = valueOrEmpty(source.paginationNextCursorJsonPath);
    input("draft-source-headers").value = json(source.headers || {});
    input("draft-source-auth-mode").value = authMode;
    input("draft-source-oauth-token-url").value = valueOrEmpty(
      (source.oauth || {}).tokenUrl || DEFAULT_OAUTH_TOKEN_URL
    );
    input("draft-source-oauth-client-id").value = valueOrEmpty((source.oauth || {}).clientId);
    input("draft-source-oauth-client-secret-ref").value = valueOrEmpty(
      (source.oauth || {}).clientSecretRef
    );
    input("draft-source-oauth-client-auth-method").value = valueOrEmpty(
      (source.oauth || {}).clientAuthMethod || DEFAULT_OAUTH_CLIENT_AUTH_METHOD
    );
    input("draft-source-oauth-scopes").value = ((source.oauth || {}).scopes || []).join(", ");
    input("draft-source-oauth-audience").value = valueOrEmpty((source.oauth || {}).audience);

    input("draft-id-field").value = valueOrEmpty(mapping.idField);
    input("draft-title-field").value = valueOrEmpty(mapping.titleField);
    input("draft-content-template").value = valueOrEmpty(mapping.contentTemplate);
    input("draft-uri-template").value = valueOrEmpty(mapping.uriTemplate);
    input("draft-mime-type").value = valueOrEmpty(mapping.mimeType || "text/plain");
    input("draft-acl-users-field").value = valueOrEmpty(mapping.aclUsersField);
    input("draft-acl-groups-field").value = valueOrEmpty(mapping.aclGroupsField);
    input("draft-metadata-fields").value = (mapping.metadataFields || []).join(", ");

    input("draft-output-bucket").value = valueOrEmpty(output.bucket);
    input("draft-output-prefix").value = valueOrEmpty(output.prefix);
    input("draft-output-format").value = valueOrEmpty(output.format || "ndjson");
    input("draft-project").value = valueOrEmpty(gemini.projectId);
    input("draft-location").value = valueOrEmpty(gemini.location);
    input("draft-datastore").value = valueOrEmpty(gemini.dataStoreId);
    input("draft-delete-policy").value = valueOrEmpty(
      reconciliation.deletePolicy || "auto_delete_missing"
    );
  }

  function buildSourceConfig(modeValue) {
    var source = {
      type: input("draft-source-type").value,
      secretRef: input("draft-secret-ref").value.trim(),
    };

    if (modeValue === "sql_pull") {
      source.query = input("draft-source-query").value.trim() || DEFAULT_SQL_QUERY;
      source.watermarkField =
        input("draft-source-watermark").value.trim() || DEFAULT_WATERMARK_FIELD;
      source.url = null;
      source.method = "GET";
      source.payload = null;
      source.paginationCursorField = null;
      source.paginationNextCursorJsonPath = null;
      source.headers = {};
      return source;
    }

    if (modeValue === "rest_pull") {
      var payload = parseJsonField("draft-source-payload", "Payload JSON", null);
      if (payload !== null && (typeof payload !== "object" || Array.isArray(payload))) {
        throw new Error("Payload JSON must be an object or null");
      }

      var headersRaw = parseJsonField("draft-source-headers", "Headers JSON", {});
      if (!headersRaw || typeof headersRaw !== "object" || Array.isArray(headersRaw)) {
        throw new Error("Headers JSON must be an object");
      }
      var normalizedHeaders = {};
      Object.keys(headersRaw).forEach(function (key) {
        normalizedHeaders[key] = String(headersRaw[key]);
      });

      source.query = null;
      source.url = input("draft-source-url").value.trim() || DEFAULT_REST_URL;
      source.method = input("draft-source-method").value || "GET";
      source.watermarkField =
        input("draft-source-watermark").value.trim() || DEFAULT_WATERMARK_FIELD;
      source.payload = payload;
      source.paginationCursorField = input("draft-source-pagination-cursor").value.trim() || null;
      source.paginationNextCursorJsonPath =
        input("draft-source-pagination-next").value.trim() || null;
      source.headers = normalizedHeaders;
      var authMode = input("draft-source-auth-mode").value || DEFAULT_REST_AUTH_MODE;
      if (authMode === "oauth_client_credentials") {
        var tokenUrl = input("draft-source-oauth-token-url").value.trim();
        var clientId = input("draft-source-oauth-client-id").value.trim();
        if (!tokenUrl) {
          throw new Error("OAuth Token URL is required when oauth_client_credentials is enabled");
        }
        if (!clientId) {
          throw new Error("OAuth Client ID is required when oauth_client_credentials is enabled");
        }
        var clientSecretRef = input("draft-source-oauth-client-secret-ref").value.trim();
        source.oauth = {
          grantType: "client_credentials",
          tokenUrl: tokenUrl,
          clientId: clientId,
          clientAuthMethod:
            input("draft-source-oauth-client-auth-method").value ||
            DEFAULT_OAUTH_CLIENT_AUTH_METHOD,
          scopes: parseScopes(input("draft-source-oauth-scopes").value),
          audience: input("draft-source-oauth-audience").value.trim() || null,
        };
        if (clientSecretRef) {
          source.oauth.clientSecretRef = clientSecretRef;
        }
      }
      return source;
    }

    source.type = "http";
    source.query = null;
    source.watermarkField = null;
    source.url = null;
    source.method = "GET";
    source.payload = null;
    source.paginationCursorField = null;
    source.paginationNextCursorJsonPath = null;
    source.headers = {};
    return source;
  }

  function buildMappingConfig() {
    return {
      idField: input("draft-id-field").value.trim(),
      titleField: input("draft-title-field").value.trim(),
      contentTemplate: input("draft-content-template").value,
      uriTemplate: input("draft-uri-template").value.trim() || null,
      mimeType: input("draft-mime-type").value.trim() || "text/plain",
      aclUsersField: input("draft-acl-users-field").value.trim() || null,
      aclGroupsField: input("draft-acl-groups-field").value.trim() || null,
      metadataFields: parseMetadataFields(input("draft-metadata-fields").value),
    };
  }

  function collectDraft() {
    var name = input("draft-name").value.trim();
    var modeValue = input("draft-mode").value;
    refreshModeState(modeValue);

    var draft = loadedDraft
      ? cloneValue(loadedDraft)
      : {
          metadata: {},
          spec: {},
          schedule: {},
        };

    draft.metadata = draft.metadata || {};
    draft.spec = draft.spec || {};
    draft.spec.source = buildSourceConfig(modeValue);
    draft.spec.mapping = buildMappingConfig();
    draft.spec.output = {
      bucket: input("draft-output-bucket").value.trim(),
      prefix: input("draft-output-prefix").value.trim(),
      format: input("draft-output-format").value.trim() || "ndjson",
    };
    draft.spec.gemini = {
      projectId: input("draft-project").value.trim(),
      location: input("draft-location").value.trim(),
      dataStoreId: input("draft-datastore").value.trim(),
    };
    draft.spec.reconciliation = {
      deletePolicy: input("draft-delete-policy").value || "auto_delete_missing",
    };
    draft.schedule = draft.schedule || {};

    draft.metadata.name = name;
    draft.spec.mode = modeValue;

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
  } else {
    refreshModeState(input("draft-mode").value, input("draft-source-auth-mode").value);
  }

  var modeSelect = input("draft-mode");
  if (modeSelect) {
    modeSelect.addEventListener("change", function () {
      refreshModeState(modeSelect.value, input("draft-source-auth-mode").value);
    });
    refreshModeState(modeSelect.value, input("draft-source-auth-mode").value);
  }

  var authModeSelect = input("draft-source-auth-mode");
  if (authModeSelect) {
    authModeSelect.addEventListener("change", function () {
      refreshModeState(input("draft-mode").value, authModeSelect.value);
    });
  }

  var validateButton = document.getElementById("draft-validate");
  if (validateButton) {
    validateButton.addEventListener("click", function () {
      try {
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
      } catch (err) {
        text("studio-output", String(err), true);
      }
    });
  }

  var previewButton = document.getElementById("draft-preview");
  if (previewButton) {
    previewButton.addEventListener("click", function () {
      try {
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
      } catch (err) {
        text("studio-output", String(err), true);
      }
    });
  }

  var proposeButton = document.getElementById("draft-propose");
  if (proposeButton) {
    proposeButton.addEventListener("click", function () {
      try {
        var action = mode;
        if (!["create", "edit", "clone", "delete", "pause", "resume"].includes(action)) {
          action = "create";
        }
        var draft = collectDraft();
        var payload = {
          action: action,
          connector_id: connectorId || draft.metadata.name,
        };
        if (["create", "edit", "clone"].includes(action)) {
          payload.draft = draft;
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
      } catch (err) {
        text("studio-output", String(err), true);
      }
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
