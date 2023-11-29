import { useState } from "react";
import { Stack, TextField, Dropdown, IDropdownOption, MessageBar, MessageBarType } from "@fluentui/react";
import { Button } from "@fluentui/react-components";
import { Attach24Filled, Send28Filled } from "@fluentui/react-icons";
import { DocumentMetaData, DocumentUploadRequest } from "../../api/models";
import { SummaryModal } from "../SummaryModal";

import styles from "./DocumentInput.module.css";

interface Props {
    disabled: boolean;
    availableDocuments: DocumentMetaData[];
    selectedDocument: DocumentMetaData | null;
    setSelectedDocument: (document: DocumentMetaData | null) => void;
}

export const DocumentInput = ({ disabled, availableDocuments, selectedDocument, setSelectedDocument }: Props) => {
    const [category, setCategory] = useState<IDropdownOption>({ key: "Default", text: "Select Category" });
    const [summaryModalShow, setSummaryModalShow] = useState<boolean>(false);
    const categoryOptions: IDropdownOption[] = availableDocuments
        ? availableDocuments
              .map(document => {
                  return { key: document.category, text: document.category };
              })
              .filter((option, index, self) => index === self.findIndex(t => t.key === option.key && t.text === option.text))
        : [];
    const documentOptions: IDropdownOption[] = availableDocuments
        ?.filter(d => d.category === category.text)
        .map(d => {
            return { key: d.id, text: `${d.title} - (${d.filename})` };
        });

    const [errors, setErrors] = useState<string[]>([]);

    return (
        <Stack className={styles.documentInputContainer}>
            {errors.length > 0 &&
                errors.map(error => (
                    <MessageBar messageBarType={MessageBarType.error} isMultiline={false} dismissButtonAriaLabel="Close">
                        {error}
                    </MessageBar>
                ))}
            {selectedDocument && summaryModalShow && (
                <SummaryModal summary={selectedDocument.summary} isOpen={summaryModalShow} setIsOpen={setSummaryModalShow} />
            )}
            <div>
                <Dropdown
                    options={categoryOptions}
                    className={styles.categorySelect}
                    placeholder="Select Category"
                    selectedKey={category.key}
                    onChange={(e, option) => {
                        setCategory(option ? option : { key: "Default", text: "Select Category" });
                    }}
                    required={true}
                />
                <Dropdown
                    options={documentOptions}
                    className={styles.documentSelect}
                    disabled={category.key === "Default"}
                    placeholder="Select Existing Document"
                    selectedKey={selectedDocument?.id || null}
                    onChange={(e, option) => {
                        setSelectedDocument(option ? availableDocuments.find(document => document.id === option.key)! : null);
                        setSummaryModalShow(true);
                    }}
                    required={true}
                />
            </div>
        </Stack>
    );
};
