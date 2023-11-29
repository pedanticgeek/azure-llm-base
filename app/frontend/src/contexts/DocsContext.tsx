import React, { createContext, useContext, useState, ReactNode } from "react";
import { DocumentMetaData } from "../api/models";

interface DocsContextType {
    documents: DocumentMetaData[];
    setDocuments: React.Dispatch<React.SetStateAction<DocumentMetaData[]>>;
}

interface DocsProviderProps {
    children: ReactNode;
}

export const DocsContext = createContext<DocsContextType>({ documents: [], setDocuments: () => {} });

export const DocsProvider: React.FC<DocsProviderProps> = ({ children }) => {
    const [documents, setDocuments] = useState<DocumentMetaData[]>([]);

    return <DocsContext.Provider value={{ documents, setDocuments }}>{children}</DocsContext.Provider>;
};

export const useDocs = () => useContext(DocsContext);
