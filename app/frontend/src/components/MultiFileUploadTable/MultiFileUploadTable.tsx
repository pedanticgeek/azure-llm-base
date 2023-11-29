import { useState } from "react";
import { DetailsList, DetailsListLayoutMode, IColumn, Toggle, DefaultButton, Spinner, SpinnerSize } from "@fluentui/react";
import { Delete16Regular } from "@fluentui/react-icons";
import { DocumentUploadRequest, acceptedFileTypes, DocumentMetaData, DocumentUploadResponse } from "../../api/models";
import { uploadDocumentsApi } from "../../api";
import { FileWithBuffer } from "../MultiFileInput/MultiFileInput";
import { useLogin, getToken } from "../../authConfig";
import { useMsal } from "@azure/msal-react";

import styles from "./MultiFileUploadTable.module.css";

interface Props {
    existingFiles: DocumentMetaData[];
    files: FileWithBuffer[];
}

interface Status {
    state: string;
    message?: string;
}

interface DocumentUpload extends DocumentUploadRequest {
    filesize: number;
    filetype?: string;
    status?: Status | null;
}

function getMB(byteLength: number) {
    return Math.round((100 * byteLength) / 1024 / 1024) / 100;
}

export const MultiFileUploadTable = ({ files, existingFiles }: Props) => {
    const [loading, setLoading] = useState<boolean>(false);
    const [filesToUpload, setFilesToUpload] = useState<DocumentUpload[]>(
        files?.map(f => {
            let res = {
                filename: f.file.name,
                fileContent: f.arrayBuffer,
                filesize: f.arrayBuffer.byteLength,
                filetype: f.file.name.split(".")?.pop(),
                status: null,
                scan: false
            };
            return { ...res, status: verify(res) } as DocumentUpload;
        })
    );

    const client = useLogin ? useMsal().instance : undefined;

    function verify(file: DocumentUpload): Status {
        if (!file.filetype) {
            return { state: "error", message: "Error: File type not found" };
        }
        if (!acceptedFileTypes.includes(file.filetype)) {
            return { state: "error", message: "Error: File type not accepted" };
        }
        if (getMB(file.filesize) > 10) {
            return { state: "error", message: "Error: File size too large" };
        }
        if (existingFiles.map(f => f.filename).includes(file.filename)) {
            return { state: "error", message: "Error: File with this name already exists" };
        }
        if (["csv", "xls", "xlsx"].includes(file.filetype)) {
            return { state: "error", message: "Error: Tabular data is not yet supported" };
        }
        return { state: "ready", message: "Ready to upload" };
    }

    const processFiles = async () => {
        setLoading(true);
        const token = client ? await getToken(client) : undefined;
        setFilesToUpload(filesToUpload.map(file => ({ ...file, status: { state: "uploading", message: "Uploading..." } })));
        const result: DocumentUploadResponse[] = await uploadDocumentsApi(filesToUpload, token?.accessToken);
        setFilesToUpload(filesToUpload.map(file => ({ ...file, status: { state: "processing", message: "Processing..." } })));
    };

    const columns: IColumn[] = [
        {
            key: "delete",
            name: "",
            fieldName: "delete",
            minWidth: 30,
            maxWidth: 30,
            isIconOnly: true,
            columnActionsMode: 0,
            onRender: (f: any) => {
                return (
                    <Delete16Regular
                        onClick={() => {
                            if (filesToUpload.length === 1) {
                                window.location.reload();
                            } else {
                                setFilesToUpload(filesToUpload.filter(file => file.filename !== f.filename));
                            }
                        }}
                        className={styles.deleteButton}
                    />
                );
            }
        },
        {
            key: "filename",
            name: "Filename",
            fieldName: "filename",
            minWidth: 100,
            maxWidth: 200,
            isResizable: true
        },
        {
            key: "filesize",
            name: "File size",
            fieldName: "filesize",
            minWidth: 40,
            maxWidth: 60,
            isResizable: true,
            onRender: (f: any) => {
                return <span>{getMB(f.filesize)} MB</span>;
            }
        },
        {
            key: "filetype",
            name: "File type",
            fieldName: "filetype",
            minWidth: 40,
            maxWidth: 60,
            isResizable: true
        },
        {
            key: "scan",
            name: "V-Scan ?",
            fieldName: "scan",
            minWidth: 60,
            maxWidth: 80,
            isResizable: true,
            columnActionsMode: 0,
            onRender: (f: any) => {
                return (
                    <Toggle
                        onText="On"
                        offText="Off"
                        checked={f.scan}
                        onChange={(ev, checked) => {
                            setFilesToUpload(filesToUpload.map(file => (file.filename === f.filename ? { ...file, scan: checked || false } : file)));
                        }}
                    />
                );
            }
        },
        {
            key: "status",
            name: "Status",
            fieldName: "status",
            minWidth: 100,
            maxWidth: 200,
            isResizable: true,
            columnActionsMode: 0,
            onRender(f: any) {
                if (f.status.state === "error") {
                    return <span className={styles.errorStatus}>{f.status.message}</span>;
                }
                if (f.status.state === "action") {
                    return <span className={styles.actionStatus}>Action Required: {f.status.message}</span>;
                }
                if (f.status.state === "ready") {
                    return <span className={styles.readyStatus}>{f.status.message}</span>;
                }
                if (f.status.state === "processing") {
                    return <Spinner className={styles.processingStatus} size={SpinnerSize.xSmall} label={f.status.message} labelPosition="right" />;
                }
                if (f.status.state === "success") {
                    return <span className={styles.successStatus}>{f.status.message}</span>;
                }
            }
        }
    ];

    return (
        <div className={styles.multiFileContainer}>
            <DefaultButton text="Upload All" onClick={processFiles} className={styles.uploadAllButton} disabled={loading} />
            <DetailsList items={filesToUpload} columns={columns} layoutMode={DetailsListLayoutMode.justified} selectionMode={0} />
        </div>
    );
};
