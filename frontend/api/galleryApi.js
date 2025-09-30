import api from "./api.js";

export const getGallery = async (sessionId) => {
    const { data } = await api.get(`/gallery/${sessionId}`);
    return data; // { session_id, count, items: [...] }
};
