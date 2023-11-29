import { useState } from "react";
import { Stack, Dropdown, DefaultButton, ProgressIndicator, MessageBar, MessageBarType } from "@fluentui/react";

import styles from "./Delete.module.css";

import { deleteDocumentApi } from "../../api";
import { useLogin, getToken } from "../../authConfig";
import { useMsal } from "@azure/msal-react";
import { useDocs } from "../../contexts/DocsContext";

export function Component(): JSX.Element {
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<boolean | null>(null);

    const { documents, setDocuments } = useDocs();
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [showVerify, setShowVerify] = useState<boolean>(false);

    const client = useLogin ? useMsal().instance : undefined;

    const deleteDocument = async () => {
        if (!selectedFile) {
            return;
        }
        error && setError(null);
        success && setSuccess(null);
        setIsLoading(true);
        setShowVerify(false);
        const token = client ? await getToken(client) : undefined;

        try {
            const result = await deleteDocumentApi({ filename: selectedFile }, token?.accessToken);
            if (!result.ok || result.status !== 200) {
                throw new Error("Failed to delete document");
            }
            setDocuments(documents.filter(f => f.filename !== selectedFile));
            setSuccess(true);
        } catch (e) {
            setError(`${e}`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.uploadsContainer}>
            <h2 className={styles.chatEmptyStateSubtitle}>Delete...</h2>
            <Stack className={styles.documentInputContainer}>
                <Dropdown
                    options={documents.map(f => ({ key: f.filename, text: f.filename }))}
                    disabled={isLoading}
                    className={styles.documentInputTextArea}
                    placeholder="Select File"
                    selectedKey={selectedFile}
                    onChange={(e, option) => {
                        setSuccess(null);
                        setError(null);
                        setSelectedFile(option?.text || null);
                    }}
                    required={true}
                />
                {isLoading ? (
                    <ProgressIndicator label="Loading..." />
                ) : (
                    <div className={styles.deleteButtonContainer}>
                        {showVerify ? (
                            <div>
                                <DefaultButton text={"Verify"} disabled={isLoading} onClick={deleteDocument} className={styles.deleteButton}></DefaultButton>
                                <DefaultButton
                                    text={"Cancel"}
                                    disabled={isLoading}
                                    onClick={() => setShowVerify(false)}
                                    className={styles.cancelButton}
                                ></DefaultButton>
                            </div>
                        ) : (
                            <DefaultButton
                                text={"Delete"}
                                disabled={isLoading}
                                onClick={() => setShowVerify(true)}
                                className={styles.deleteButton}
                            ></DefaultButton>
                        )}
                    </div>
                )}
                {error && (
                    <MessageBar messageBarType={MessageBarType.error} dismissButtonAriaLabel="Close">
                        {error}
                    </MessageBar>
                )}
                {success && (
                    <MessageBar messageBarType={MessageBarType.success} dismissButtonAriaLabel="Close">
                        Successfully deleted the file
                    </MessageBar>
                )}
            </Stack>
        </div>
    );
}

Component.displayName = "uploads";
