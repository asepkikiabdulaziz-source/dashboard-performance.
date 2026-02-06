const hasWindow = typeof window !== 'undefined';

const canUseLocalStorage = () => {
    if (!hasWindow || !window.localStorage) {
        return false;
    }

    try {
        const testKey = '__storage_test__';
        window.localStorage.setItem(testKey, '1');
        window.localStorage.removeItem(testKey);
        return true;
    } catch (error) {
        return false;
    }
};

let storageAvailable;

const isStorageAvailable = () => {
    if (storageAvailable === undefined) {
        storageAvailable = canUseLocalStorage();
    }
    return storageAvailable;
};

export const storageGetItem = (key) => {
    if (!isStorageAvailable()) {
        return null;
    }

    try {
        return window.localStorage.getItem(key);
    } catch (error) {
        return null;
    }
};

export const storageSetItem = (key, value) => {
    if (!isStorageAvailable()) {
        return false;
    }

    try {
        window.localStorage.setItem(key, value);
        return true;
    } catch (error) {
        return false;
    }
};

export const storageRemoveItem = (key) => {
    if (!isStorageAvailable()) {
        return false;
    }

    try {
        window.localStorage.removeItem(key);
        return true;
    } catch (error) {
        return false;
    }
};

export const storageGetJSON = (key) => {
    const value = storageGetItem(key);
    if (!value) {
        return null;
    }

    try {
        return JSON.parse(value);
    } catch (error) {
        storageRemoveItem(key);
        return null;
    }
};

export const clearAuthStorage = () => {
    storageRemoveItem('access_token');
    storageRemoveItem('user');
};
