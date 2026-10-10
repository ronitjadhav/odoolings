/**
 * Which deep-dive chapters go deeper into a journey chapter's topic.
 *
 * The journey (chapters 1 to 55) gives each topic one pass; a deep dive takes one
 * domain all the way down. This map is what puts a "Go deeper" card at the end of a
 * journey chapter. Chapters listed here that are not written yet render as "coming",
 * so a reader sees where the depth will be without hitting a dead link.
 */
export interface DeepDiveTrack {
  id: string; // "inv"
  name: string; // "Inventory"
  entry: string; // id of the first chapter, the place to start the track
  chapters: Record<string, string>; // id -> planned title, for chapters not written yet
}

export const TRACKS: DeepDiveTrack[] = [
  {
    id: 'inv',
    name: 'Inventory',
    entry: 'inv01',
    chapters: {
      inv01: 'The Warehouse Map',
      inv02: "A Transfer's Life",
      inv03: 'Routes and Rules, the Engine',
      inv04: 'Manufacturing Meets the Warehouse',
      inv05: 'Replenishment, Properly',
      inv06: 'More Than One Warehouse',
      inv07: 'Traceability: Lots, Serials, Expiry',
      inv08: 'Packages, Packagings and Barcodes',
      inv09: 'Where Things Go, Where They Come From',
      inv10: 'Counting, Correcting, Scrapping, Batching',
      inv11: 'Beyond the Four Walls',
      inv12: 'Valuation, the Full Story',
      inv13: 'The Code Underneath',
      inv14: 'Extending Inventory Safely',
      inv15: 'Inventory on a Real Project',
    },
  },
];

/** journey chapter id -> deep-dive chapter ids that go deeper into it */
export const GO_DEEPER: Record<string, string[]> = {
  '21': ['inv01'],
  '22': ['inv02'],
  '24': ['inv02', 'inv11'],
  '25': ['inv01', 'inv02', 'inv03', 'inv05', 'inv06'],
  '26': ['inv04'],
  '30': ['inv12'],
  '53': ['inv15'],
};

export function trackOf(chapterId: string): DeepDiveTrack | undefined {
  return TRACKS.find((t) => chapterId.startsWith(t.id));
}
