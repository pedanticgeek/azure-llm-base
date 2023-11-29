import { useState } from "react";
import { Stack, TextField } from "@fluentui/react";
import { Button } from "@fluentui/react-components";
import { Attach24Filled, Send28Filled } from "@fluentui/react-icons";
import styles from "./MultiFileInput.module.css";
import { acceptedFileTypes } from "../../api/models";

interface Props {
    disabled: boolean;
    setDocuments: (files: FileWithBuffer[] | null) => void;
}

export type FileWithBuffer = {
    file: File;
    arrayBuffer: ArrayBuffer;
};

export const MultiFileInput = ({ disabled, setDocuments }: Props) => {
    const [filesUpload, setFilesUpload] = useState<FileWithBuffer[]>([]);

    const onFilesChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (files) {
            const fileReaders: Promise<FileWithBuffer>[] = [];

            Array.from(files).forEach(file => {
                const reader = new FileReader();

                const fileReaderPromise = new Promise<FileWithBuffer>(resolve => {
                    reader.onload = (readEvent: ProgressEvent<FileReader>) => {
                        resolve({
                            file: file,
                            arrayBuffer: readEvent.target?.result as ArrayBuffer
                        });
                    };
                });

                reader.readAsArrayBuffer(file);
                fileReaders.push(fileReaderPromise);
            });

            Promise.all(fileReaders).then(newFiles => {
                setFilesUpload(prevFiles => [...prevFiles, ...newFiles]);
            });
        }
    };

    return (
        <Stack className={styles.documentInputContainer}>
            <Stack>
                <Stack horizontal>
                    <div className={styles.documentInputTextArea}>
                        <TextField
                            placeholder="Select Documents"
                            resizable={false}
                            borderless
                            value={filesUpload.map(f => f.file.name).join("\n")}
                            readOnly
                            autoAdjustHeight
                            multiline
                        />
                    </div>
                    <div className={styles.documentInputButtonsContainer}>
                        <input
                            type="file"
                            id="fileInput"
                            accept={acceptedFileTypes.map(t => `.${t}`).join(", ")}
                            style={{ display: "none" }}
                            onChange={onFilesChange}
                            multiple
                        />
                        <label htmlFor="fileInput" className={styles.documentInputButton}>
                            <Button
                                size="large"
                                icon={<Attach24Filled primaryFill="rgba(115, 118, 225, 1)" />}
                                disabled={disabled}
                                onClick={() => document.getElementById("fileInput")?.click()}
                            />
                        </label>
                        <Button
                            size="large"
                            icon={<Send28Filled primaryFill="rgba(115, 118, 225, 1)" />}
                            disabled={disabled || !filesUpload}
                            onClick={() => setDocuments(filesUpload)}
                        />
                    </div>{" "}
                </Stack>
            </Stack>
        </Stack>
    );
};
