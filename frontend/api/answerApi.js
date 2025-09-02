// import api from "./api";

// /**
//  * Send the user's choice for a given year.
//  * 
//  * @param {number|string} year - The current story year
//  * @param {string} choice - The user's selected choice
//  * @returns {Promise<object>} The result and next scenario/question
//  */
// export const submitChoice = async (year, choice) => {
//   try {
//     const response = await api.post("/storyline/result", {
//       params: { year, choice }
//     });
//     return response.data;
//   } catch (error) {
//     console.error("Error submitting choice:", error);
//     throw error;
//   }
// };

// UNCOMMENT ABOVE CODE, THIS IS ONLY FOR TESTING PURPOSES:

import api from "./api";

/**
 * Send the user's choice for a given year (multiplayer-aware).
 * @param {number} year
 * @param {string} choice  option id (e.g. "yes"/"no")
 * @param {string} clientId stable anonymous id for this device
 * @param {number} players  1 for single, 2 for multiplayer
 */
export const submitChoice = async (year, choice, clientId, players = 1) => {
  const { data } = await api.post("/storyline/result", { year, choice, clientId, players });
  return data;
};
