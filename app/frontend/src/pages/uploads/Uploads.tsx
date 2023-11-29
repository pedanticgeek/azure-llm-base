import { useState } from "react";

import styles from "./Uploads.module.css";

import { MultiFileInput, FileWithBuffer } from "../../components/MultiFileInput";
import { MultiFileUploadTable } from "../../components/MultiFileUploadTable";
import { useDocs } from "../../contexts/DocsContext";

export function Component(): JSX.Element {
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [files, setFiles] = useState<FileWithBuffer[] | null>(null);

    const { documents } = useDocs();

    return (
        <div className={styles.uploadsContainer}>
            <h2 className={styles.chatEmptyStateSubtitle}>Uploads</h2>
            {files && files.length > 0 ? (
                <div className={styles.uploadsDocumentsTable}>
                    <MultiFileUploadTable files={files} existingFiles={documents} />
                </div>
            ) : (
                <div className={styles.uploadsDocumentsInput}>
                    <MultiFileInput disabled={isLoading} setDocuments={setFiles} />
                </div>
            )}
        </div>
    );
}

Component.displayName = "uploads";
