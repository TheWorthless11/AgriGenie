/*
 * Reusable Leaflet + OpenStreetMap location picker.
 * Supports reverse geocoding and optional wiring to dropdown/text fields.
 */
(function (window) {
  'use strict';

  function trim(value) {
    return (value || '').toString().trim();
  }

  function getElement(id) {
    if (!id) {
      return null;
    }
    return document.getElementById(id);
  }

  function pickFirst(source, keys) {
    if (!source) {
      return '';
    }

    for (var i = 0; i < keys.length; i += 1) {
      var key = keys[i];
      var value = trim(source[key]);
      if (value) {
        return value;
      }
    }
    return '';
  }

  function normalizeAdminName(value) {
    return trim(value)
      .toLowerCase()
      .replace(/\b(division|district|state|province|region|county|city)\b/g, '')
      .replace(/[^a-z0-9\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function setSelectValue(selectEl, rawValue) {
    if (!selectEl || !trim(rawValue)) {
      return false;
    }

    var target = trim(rawValue);
    var targetLower = target.toLowerCase();
    var targetNormalized = normalizeAdminName(target);

    var options = selectEl.options || [];
    var i;

    for (i = 0; i < options.length; i += 1) {
      if (trim(options[i].value) === target) {
        selectEl.value = options[i].value;
        return true;
      }
    }

    for (i = 0; i < options.length; i += 1) {
      if (trim(options[i].value).toLowerCase() === targetLower) {
        selectEl.value = options[i].value;
        return true;
      }
    }

    for (i = 0; i < options.length; i += 1) {
      var normalizedOption = normalizeAdminName(options[i].value || options[i].textContent);
      if (normalizedOption && normalizedOption === targetNormalized) {
        selectEl.value = options[i].value;
        return true;
      }
    }

    return false;
  }

  function setInputValue(el, value) {
    if (!el || value === null || value === undefined) {
      return;
    }

    el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function formatStreet(address) {
    if (!address) {
      return '';
    }

    var house = trim(address.house_number);
    var road = trim(address.road) || trim(address.pedestrian) || trim(address.footway);
    var suburb = trim(address.suburb) || trim(address.neighbourhood);

    var parts = [];
    if (house && road) {
      parts.push(house + ' ' + road);
    } else if (road) {
      parts.push(road);
    } else if (house) {
      parts.push(house);
    }

    if (suburb) {
      parts.push(suburb);
    }

    return parts.join(', ');
  }

  async function fetchJson(url) {
    try {
      var response = await fetch(url, {
        headers: {
          Accept: 'application/json'
        }
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch (error) {
      return null;
    }
  }

  async function reverseGeocode(lat, lng) {
    var url =
      'https://nominatim.openstreetmap.org/reverse?format=jsonv2&addressdetails=1&lat=' +
      encodeURIComponent(lat) +
      '&lon=' +
      encodeURIComponent(lng);

    var result = await fetchJson(url);
    if (!result || !result.address) {
      return null;
    }

    return result;
  }

  async function forwardGeocode(query) {
    if (!trim(query)) {
      return null;
    }

    var url =
      'https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=' +
      encodeURIComponent(query);

    var results = await fetchJson(url);
    if (!Array.isArray(results) || !results.length) {
      return null;
    }

    var first = results[0];
    var lat = Number(first.lat);
    var lon = Number(first.lon);

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      return null;
    }

    return {
      lat: lat,
      lon: lon
    };
  }

  function buildDisplayAddress(result, fallbackCountry, fallbackState, fallbackCity) {
    var display = trim(result && result.display_name);
    if (display) {
      return display;
    }

    return [fallbackCity, fallbackState, fallbackCountry].filter(Boolean).join(', ');
  }

  async function applyFieldsFromCoordinates(config, lat, lng) {
    var result = await reverseGeocode(lat, lng);
    if (!result) {
      return;
    }

    var address = result.address || {};
    var street = formatStreet(address);
    var postalCode = pickFirst(address, ['postcode']);
    var country = pickFirst(address, ['country']);
    var state = pickFirst(address, ['state', 'state_district', 'province', 'region', 'county']);
    var city = pickFirst(address, ['city', 'town', 'village', 'municipality', 'suburb', 'county']);
    var displayAddress = buildDisplayAddress(result, country, state, city);

    var streetField = getElement(config.streetFieldId);
    var postalField = getElement(config.postalFieldId);
    if (streetField) {
      setInputValue(streetField, street);
    }
    if (postalField) {
      setInputValue(postalField, postalCode);
    }

    var fullAddressFieldIds = Array.isArray(config.fullAddressFieldIds)
      ? config.fullAddressFieldIds
      : [];
    fullAddressFieldIds.forEach(function (fieldId) {
      var el = getElement(fieldId);
      if (el) {
        setInputValue(el, displayAddress);
      }
    });

    var countryEl = getElement(config.countryFieldId);
    var stateEl = getElement(config.stateFieldId);
    var cityEl = getElement(config.cityFieldId);

    if (countryEl && country) {
      var countrySet = setSelectValue(countryEl, country);
      if (countrySet) {
        countryEl.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }

    window.setTimeout(function () {
      if (stateEl && state) {
        var stateSet = setSelectValue(stateEl, state);
        if (stateSet) {
          stateEl.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }

      window.setTimeout(function () {
        if (cityEl && city) {
          setSelectValue(cityEl, city);
        }
      }, 150);
    }, 150);
  }

  window.initLocationMapPicker = function initLocationMapPicker(config) {
    if (!window.L) {
      return null;
    }

    var mapEl = getElement(config.mapElementId);
    if (!mapEl) {
      return null;
    }

    var defaultLat = Number(config.defaultLat);
    var defaultLng = Number(config.defaultLng);
    var zoom = Number(config.zoom);

    if (!Number.isFinite(defaultLat)) {
      defaultLat = 23.8103;
    }
    if (!Number.isFinite(defaultLng)) {
      defaultLng = 90.4125;
    }
    if (!Number.isFinite(zoom)) {
      zoom = 12;
    }

    var map = window.L.map(mapEl).setView([defaultLat, defaultLng], zoom);
    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    var marker = window.L.marker([defaultLat, defaultLng], {
      draggable: true
    }).addTo(map);

    var placeholder = getElement(config.placeholderId);
    if (placeholder) {
      placeholder.style.display = 'none';
    }

    var updateFromCoords = async function (lat, lng) {
      marker.setLatLng([lat, lng]);
      await applyFieldsFromCoordinates(config, lat, lng);
    };

    marker.on('dragend', function () {
      var position = marker.getLatLng();
      updateFromCoords(position.lat, position.lng);
    });

    map.on('click', function (event) {
      updateFromCoords(event.latlng.lat, event.latlng.lng);
    });

    var initialAddressField = getElement(config.initialAddressFieldId);
    var initialAddress = trim(config.initialAddressText);
    if (initialAddressField && trim(initialAddressField.value)) {
      initialAddress = trim(initialAddressField.value);
    }

    if (initialAddress) {
      forwardGeocode(initialAddress).then(function (coords) {
        if (coords) {
          marker.setLatLng([coords.lat, coords.lon]);
          map.setView([coords.lat, coords.lon], zoom);
        }
      });
    } else if (config.resolveDefaultAddress) {
      updateFromCoords(defaultLat, defaultLng);
    }

    window.setTimeout(function () {
      map.invalidateSize();
    }, 120);

    return {
      map: map,
      marker: marker,
      updateFromCoords: updateFromCoords
    };
  };
})(window);