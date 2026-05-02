const PROFILE_KEY = "safebite_user_profile";

const defaultUserProfile = {
  allergens: [],
  conditions: [],
  avoided_ingredients: [],
  preferred_ingredients: [],
};

export function getSavedUserProfile() {
  try {
    const raw = localStorage.getItem(PROFILE_KEY);

    if (!raw) {
      return { ...defaultUserProfile };
    }

    const parsed = JSON.parse(raw);

    return {
      allergens: Array.isArray(parsed?.allergens) ? parsed.allergens : [],
      conditions: Array.isArray(parsed?.conditions) ? parsed.conditions : [],
      avoided_ingredients: Array.isArray(parsed?.avoided_ingredients)
        ? parsed.avoided_ingredients
        : [],
      preferred_ingredients: Array.isArray(parsed?.preferred_ingredients)
        ? parsed.preferred_ingredients
        : [],
    };
  } catch {
    return { ...defaultUserProfile };
  }
}

export function saveUserProfile(profile) {
  const cleanProfile = {
    allergens: Array.isArray(profile?.allergens) ? profile.allergens : [],
    conditions: Array.isArray(profile?.conditions) ? profile.conditions : [],
    avoided_ingredients: Array.isArray(profile?.avoided_ingredients)
      ? profile.avoided_ingredients
      : [],
    preferred_ingredients: Array.isArray(profile?.preferred_ingredients)
      ? profile.preferred_ingredients
      : [],
  };

  localStorage.setItem(PROFILE_KEY, JSON.stringify(cleanProfile));
  return cleanProfile;
}

export function clearUserProfile() {
  localStorage.removeItem(PROFILE_KEY);
  return { ...defaultUserProfile };
}

export function parseCommaList(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function toCommaString(values) {
  return Array.isArray(values) ? values.join(", ") : "";
}

export function updateUserProfileField(field, value) {
  const current = getSavedUserProfile();

  const next = {
    ...current,
    [field]: Array.isArray(value) ? value : [],
  };

  return saveUserProfile(next);
}

export function getDefaultUserProfile() {
  return { ...defaultUserProfile };
}
