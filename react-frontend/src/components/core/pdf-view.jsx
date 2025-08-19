import React, {
  useEffect,
  useRef,
  useState,
  forwardRef,
  useImperativeHandle,
} from "react";
import { useSelector, useDispatch } from "react-redux";
import { getFileFromDb } from "../../services/db";
import { setTargetLocation } from "../../redux/pdfsSlice";
import toast from "react-hot-toast";

const ADOBE_SDK_URL = "https://documentcloud.adobe.com/view-sdk/main.js";

const AdobeViewerInstance = forwardRef(({ fileId }, ref) => {
  const [isReady, setIsReady] = useState(false);
  const apisRef = useRef(null);
  const dispatch = useDispatch();
  const { targetLocation } = useSelector((state) => state.pdfs);
  const viewerId = `adobe-dc-view-${fileId}`;

  useImperativeHandle(ref, () => ({
    async getCurrentPage() {
      if (apisRef.current) {
        try {
          const page = await apisRef.current.getCurrentPage();
          return page;
        } catch (error) {
          console.error("Failed to get current page:", error);
          return 1;
        }
      }
      return 1;
    },
    getSelectedText() {
      return new Promise(async (resolve, reject) => {
        if (!apisRef.current) {
          toast.error("Viewer is not ready. Please try again in a moment.");
          return resolve(null);
        }
        try {
          const result = await apisRef.current.getSelectedContent();
          if (result && result.type === "text" && result.data) {
            resolve(result.data);
          } else {
            resolve(null);
          }
        } catch (error) {
          console.error("Adobe API error on getSelectedContent:", error);
          toast.error("An error occurred while getting the selected text.");
          reject(error);
        }
      });
    },
  }));

  useEffect(() => {
    const renderPdf = () => {
      getFileFromDb(fileId)
        .then((file) => {
          if (!file) throw new Error("File not found in database.");
          const adobeDCView = new window.AdobeDC.View({
            clientId: "b891f93e9d5a4fef9a261526d2646a7c",
            divId: viewerId,
          });
          adobeDCView
            .previewFile(
              {
                content: { location: { url: URL.createObjectURL(file) } },
                metaData: { fileName: file.name },
              },
              {
                embedMode: "SIZED_CONTAINER",
                showAnnotationTools: true,
              }
            )
            .then((adobeViewer) => {
              adobeViewer.getAPIs().then((apis) => {
                apisRef.current = apis;
                setIsReady(true);
              });
            });
        })
        .catch((err) => {
          console.error("Error rendering PDF:", err);
          toast.error("Could not render the selected PDF.");
        });
    };

    if (window.AdobeDC && window.AdobeDC.View) {
      renderPdf();
    } else {
      document.addEventListener("adobe_dc_view_sdk.ready", renderPdf);
    }

    return () => {
      document.removeEventListener("adobe_dc_view_sdk.ready", renderPdf);
    };
  }, [fileId, viewerId]);

  useEffect(() => {
    if (isReady && apisRef.current && targetLocation) {
      apisRef.current
        .gotoLocation(targetLocation.page, targetLocation.x, targetLocation.y)
        .then(() => {
          console.log(`Successfully jumped to page ${targetLocation.page}`);
          dispatch(setTargetLocation(null));
        })
        .catch((error) => {
          console.error("Failed to jump to location:", error);
          dispatch(setTargetLocation(null));
        });
    }
  }, [isReady, targetLocation, dispatch]);

  return <div id={viewerId} className="w-full h-full" />;
});

const AdobePDFViewer = forwardRef(({ fileId }, ref) => {
  useEffect(() => {
    if (!document.querySelector(`script[src='${ADOBE_SDK_URL}']`)) {
      const script = document.createElement("script");
      script.src = ADOBE_SDK_URL;
      script.async = true;
      document.head.appendChild(script);
    }
  }, []);

  if (!fileId) {
    return (
      <div className="w-full h-full bg-gray-900 flex items-center justify-center">
        <p className="text-white">No document selected.</p>
      </div>
    );
  }

  return <AdobeViewerInstance key={fileId} fileId={fileId} ref={ref} />;
});

export default AdobePDFViewer;
