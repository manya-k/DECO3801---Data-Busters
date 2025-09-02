import api from "./api";

export const getStoryState = async () => {
  const { data } = await api.get("/storyline/state");
  return data; // { index, year, question, options, counts, has_next }
};
