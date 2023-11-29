import { useEffect } from "react";
import { Outlet, NavLink, Link } from "react-router-dom";

import styles from "./Layout.module.css";

import { useLogin } from "../../authConfig";

import { LoginButton } from "../../components/LoginButton";

import logo from "../../assets/logo.png";
import { useDocs } from "../../contexts/DocsContext";
import { getDocumentsStructureApi } from "../../api";

const Layout = () => {
    const { documents, setDocuments } = useDocs();

    useEffect(() => {
        const token = localStorage.getItem("token");
        const result = getDocumentsStructureApi(token || undefined);
        result.then(res => {
            setDocuments(res.documents);
        });
    }, []);
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <nav>
                        <ul className={styles.headerNavList}>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Assistant
                                </NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/uploads" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Uploads
                                </NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/delete" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Delete
                                </NavLink>
                            </li>
                        </ul>
                    </nav>{" "}
                    <Link to="/" className={styles.headerTitleContainer}>
                        <img src={logo} className={styles.headerLogo} alt="logo" />
                    </Link>
                    {useLogin && <LoginButton />}
                </div>
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
