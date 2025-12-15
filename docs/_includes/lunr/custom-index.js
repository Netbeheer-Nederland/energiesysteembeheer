// Verwijder de paginatitel uit de content die wordt geïndexeerd om dubbele resultaten te voorkomen.
// We gebruiken .replace() omdat dit robuuster is dan .startsWith().

const title = docs[i].title.trim();
const content = docs[i].content.trim();

// Vervang de eerste instantie van de titel in de content door een lege string.
docs[i].content = content.replace(title, '').trim();
