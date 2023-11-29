import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

interface Props {
    onExampleClicked: (value: string) => void;
    examples: ExampleModel[];
}

export const ExampleList = ({ onExampleClicked, examples }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {examples.map((x, i) => (
                <li key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
