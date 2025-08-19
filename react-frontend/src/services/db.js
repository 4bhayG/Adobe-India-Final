import Dexie from "dexie";

export const db = new Dexie("DocuHubDB");
db.version(1).stores({
  files: "++id, file",
});

/**
 * Adds a file to the IndexedDB.
 * @param {File} file - The file to store.
 * @returns {Promise<number>} The ID of the stored file.
 */
export async function addFileToDb(file) {
  if (!file) throw new Error("File is required");
  const id = await db.files.put({ file });
  return id;
}

/**
 * Retrieves a file from the IndexedDB by its ID.
 * @param {number} id - The ID of the file to retrieve.
 * @returns {Promise<File|null>} The File object, or null if not found.
 */
export async function getFileFromDb(id) {
  if (!id) return null;
  const result = await db.files.get(id);
  return result ? result.file : null;
}
