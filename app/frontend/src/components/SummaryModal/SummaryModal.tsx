import { useState } from "react";
import { Modal, IconButton } from "@fluentui/react";
import { mergeStyles } from "@fluentui/react/lib/Styling";

const overlayStyles = {
    root: {
        backgroundColor: "rgba(255, 255, 255, 0.5)" // White with 50% opacity
    }
};

const windowStyles = mergeStyles({
    maxWidth: "40%",
    backgroundColor: "rgba(255, 255, 255, 0.5)"
});

const contentStyles = mergeStyles({
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    margin: 20,
    padding: 20,
    borderRadius: 4,
    backgroundColor: "rgba(255, 255, 255, 0.5)",
    boxShadow: "0 0 5px rgba(0, 0, 0, 0.2)", // Optional: for shadow
    background: "white" // Or any other background color for the popup
});

interface Props {
    summary: string;
    isOpen: boolean;
    setIsOpen: (isOpen: boolean) => void;
}

export const SummaryModal = ({ summary, isOpen, setIsOpen }: Props) => {
    return (
        <Modal isOpen={isOpen} onDismiss={() => setIsOpen(false)} isBlocking={false} containerClassName={windowStyles}>
            <div className={contentStyles}>
                <p>{summary}</p>
                <IconButton iconProps={{ iconName: "Cancel" }} ariaLabel="Close popup modal" onClick={() => setIsOpen(false)} />
            </div>
        </Modal>
    );
};
