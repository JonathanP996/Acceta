import { getLanguageById, getAccentById } from '../data/languages';

const STORAGE_KEY = 'accentProfiles';
const CURRENT_PROFILE_ID_KEY = 'currentProfileId';
const CURRENT_PROFILE_KEY = 'currentProfile';
const PROFILE_LAST_UPDATED_KEY = 'profileLastUpdated';

const buildProfileId = (languageId, accentId) => `${languageId}__${accentId}`;

const normalizeProfile = (profile) => {
  if (!profile || !profile.language || !profile.accent) {
    return null;
  }

  const languageId = profile.language.id || profile.languageId;
  const accentId = profile.accent.id || profile.accentId;

  const language = getLanguageById(languageId);
  const accent = accentId ? getAccentById(languageId, accentId) : null;

  const languagePayload = language
    ? { id: language.id, name: language.name, flag: language.flag }
    : {
        id: languageId,
        name: profile.language.name || languageId,
        flag: profile.language.flag || '🌍',
      };

  const accentPayload = accent
    ? { id: accent.id, name: accent.name, difficulty: accent.difficulty }
    : {
        id: accentId,
        name:
          (typeof profile.accent === 'object' ? profile.accent.name : profile.accent) ||
          accentId ||
          'Standard',
        difficulty:
          (typeof profile.accent === 'object' && profile.accent.difficulty) || 'beginner',
      };

  const skillLevel = profile.skillLevel
    ? {
        id: profile.skillLevel.id,
        name: profile.skillLevel.name,
        min: profile.skillLevel.min,
        max: profile.skillLevel.max,
        color: profile.skillLevel.color,
      }
    : null;

  const skills = Array.isArray(profile.skills) ? profile.skills : null;

  return {
    id: profile.id || buildProfileId(languagePayload.id, accentPayload.id),
    language: languagePayload,
    accent: accentPayload,
    overallScore: profile.overallScore ?? 0,
    skillLevel,
    skills,
    totalSessions: profile.totalSessions ?? 0,
    practiceTime: profile.practiceTime ?? 0,
    struggleAreas: profile.struggleAreas ?? [],
    learningReason: profile.learningReason ?? null,
    createdAt: profile.createdAt || new Date().toISOString(),
    updatedAt: profile.updatedAt || new Date().toISOString(),
  };
};

const readProfiles = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map(normalizeProfile)
      .filter(Boolean)
      .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
  } catch (error) {
    console.error('Failed to read accent profiles:', error);
    return [];
  }
};

const writeProfiles = (profiles) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profiles));
  } catch (error) {
    console.error('Failed to write accent profiles:', error);
  }
};

const setCurrentProfile = (profile) => {
  if (!profile) {
    localStorage.removeItem(CURRENT_PROFILE_KEY);
    localStorage.removeItem(CURRENT_PROFILE_ID_KEY);
    localStorage.removeItem(PROFILE_LAST_UPDATED_KEY);
    return;
  }

  const normalized = normalizeProfile(profile);
  if (!normalized) return;

  try {
    localStorage.setItem(CURRENT_PROFILE_KEY, JSON.stringify(normalized));
    localStorage.setItem(CURRENT_PROFILE_ID_KEY, normalized.id);
    localStorage.setItem(PROFILE_LAST_UPDATED_KEY, Date.now().toString());
    window.dispatchEvent(new CustomEvent('profileChanged', { detail: normalized }));
  } catch (error) {
    console.error('Failed to set current profile:', error);
  }
};

const getCurrentProfile = () => {
  try {
    const raw = localStorage.getItem(CURRENT_PROFILE_KEY);
    if (!raw) return null;
    return normalizeProfile(JSON.parse(raw));
  } catch (error) {
    console.error('Failed to parse current profile:', error);
    return null;
  }
};

const getProfileById = (profileId) => {
  if (!profileId) return null;
  const profiles = readProfiles();
  return profiles.find((p) => p.id === profileId) || null;
};

const getProfile = (languageId, accentId) => {
  if (!languageId || !accentId) return null;
  const profileId = buildProfileId(languageId, accentId);
  return getProfileById(profileId);
};

const upsertProfile = (profilePayload) => {
  const normalized = normalizeProfile(profilePayload);
  if (!normalized) {
    throw new Error('Invalid profile payload');
  }

  const profiles = readProfiles();
  const existingIndex = profiles.findIndex((p) => p.id === normalized.id);

  const profileToStore = {
    ...normalized,
    updatedAt: new Date().toISOString(),
  };

  if (existingIndex >= 0) {
    profiles[existingIndex] = {
      ...profiles[existingIndex],
      ...profileToStore,
    };
  } else {
    profiles.push(profileToStore);
  }

  writeProfiles(profiles);
  return profileToStore;
};

const removeProfile = (profileId) => {
  if (!profileId) return;
  const profiles = readProfiles();
  const filtered = profiles.filter((p) => p.id !== profileId);
  writeProfiles(filtered);

  const currentId = localStorage.getItem(CURRENT_PROFILE_ID_KEY);
  if (currentId === profileId) {
    setCurrentProfile(filtered[0] || null);
  }
};

export const profileManager = {
  buildProfileId,
  readProfiles,
  writeProfiles,
  getCurrentProfile,
  setCurrentProfile,
  getProfile,
  getProfileById,
  upsertProfile,
  removeProfile,
};

export default profileManager;

