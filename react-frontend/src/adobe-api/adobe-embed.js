export function loadAdobeEmbed({ clientId, divId, pdfUrl, fileName }) {
  return new Promise((resolve, reject) => {
    if (!window.AdobeDC) {
      return reject(new Error("Adobe DC SDK not available."));
    }
    try {
      const adobeDCView = new window.AdobeDC.View({ clientId, divId });
      const previewFilePromise = adobeDCView.previewFile(
        {
          content: { location: { url: pdfUrl } },
          metaData: { fileName },
        },
        {}
      );
      resolve(adobeDCView);
    } catch (error) {
      console.error("Error initializing Adobe PDF viewer:", error);
      reject(error);
    }
  });
}
