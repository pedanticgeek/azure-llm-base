import React from "react";
import ReactDOM from "react-dom/client";
import { createHashRouter, RouterProvider } from "react-router-dom";
import { initializeIcons } from "@fluentui/react";
import { DocsProvider } from "./contexts/DocsContext";

import "./index.css";

import Layout from "./pages/layout/Layout";
import Chat from "./pages/chat/Chat";

var layout = <Layout />;

initializeIcons();

const router = createHashRouter([
    {
        path: "/",
        element: layout,
        children: [
            {
                path: "*",
                lazy: () => import("./pages/NoPage")
            },
            {
                path: "/",
                element: <Chat />
            },
            {
                path: "uploads",
                lazy: () => import("./pages/uploads/Uploads")
            },
            {
                path: "delete",
                lazy: () => import("./pages/delete/Delete")
            }
        ]
    }
]);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <DocsProvider>
            <RouterProvider router={router} />
        </DocsProvider>
    </React.StrictMode>
);
