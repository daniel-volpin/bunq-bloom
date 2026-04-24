const acceptedTypes = ["image/jpeg", "image/png", "image/webp"];
const maxImageBytes = 8 * 1024 * 1024;

export function validateImageFile(file: File): string | null {
  if (!acceptedTypes.includes(file.type)) {
    return "Use a JPEG, PNG, or WebP photo.";
  }

  if (file.size > maxImageBytes) {
    return "That photo is bigger than 8 MB. Try a smaller one.";
  }

  return null;
}

export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("Could not read that photo."));
    reader.readAsDataURL(file);
  });
}
