import Draggable from "react-draggable";
import { useRef, useState } from "react";
import { Form, Modal, Button, FormProps, FormInstance } from "antd";
import type { DraggableData, DraggableEvent } from "react-draggable";

const AddModal = ({
    open,
    setOpen,
    loading,
    form,
    buttonIcon,
    buttonContent,
    formTitle,
    modalContent,
    resetModalContentValues,
    formItems,
    submitButtonContent,
    onFinish,
    onFinishFailed,
}: {
    open: boolean;
    setOpen: React.Dispatch<React.SetStateAction<boolean>>;
    loading: boolean;
    form?: FormInstance;
    buttonIcon: React.ReactNode;
    buttonContent: string;
    formTitle: string;
    formItems?: React.JSX.Element | null;
    modalContent?: React.ReactNode;
    resetModalContentValues?: () => void;
    submitButtonContent: string;
    onFinish: FormProps["onFinish"];
    onFinishFailed: FormProps["onFinishFailed"];
}) => {
    const [disabled, setDisabled] = useState<boolean>(true);
    const [bounds, setBounds] = useState({
        left: 0,
        top: 0,
        bottom: 0,
        right: 0,
    });
    const draggleRef = useRef<HTMLDivElement>(null);

    const showModal = () => {
        setOpen(true);
    };

    const handleCancel = (e: React.MouseEvent<HTMLElement>) => {
        e.preventDefault();
        if (form) {
            form.resetFields();
        }
        if (resetModalContentValues) {
            resetModalContentValues();
        }
        setOpen(false);
    };

    const onStart = (_event: DraggableEvent, uiData: DraggableData) => {
        const { clientWidth, clientHeight } = window.document.documentElement;
        const targetRect = draggleRef.current?.getBoundingClientRect();
        if (!targetRect) {
            return;
        }
        setBounds({
            left: -targetRect.left + uiData.x,
            right: clientWidth - (targetRect.right - uiData.x),
            top: -targetRect.top + uiData.y,
            bottom: clientHeight - (targetRect.bottom - uiData.y),
        });
    };

    return (
        <div>
            <Button onClick={showModal} icon={buttonIcon}>
                {buttonContent}
            </Button>
            <Modal
                title={
                    <div
                        style={{
                            width: "100%",
                            cursor: "move",
                            display: "flex",
                            justifyContent: "center",
                            color: "green",
                            marginBottom: "2rem",
                        }}
                        onMouseOver={() => {
                            if (disabled) {
                                setDisabled(false);
                            }
                        }}
                        onMouseOut={() => {
                            setDisabled(true);
                        }}
                        // fix eslintjsx-a11y/mouse-events-have-key-events
                        // https://github.com/jsx-eslint/eslint-plugin-jsx-a11y/blob/master/docs/rules/mouse-events-have-key-events.md
                        onFocus={() => {}}
                        onBlur={() => {}}
                        // end
                    >
                        {formTitle}
                    </div>
                }
                onCancel={handleCancel}
                open={open}
                modalRender={(modal) => (
                    <Draggable
                        disabled={disabled}
                        bounds={bounds}
                        nodeRef={draggleRef}
                        onStart={(event, uiData) => onStart(event, uiData)}
                    >
                        <div ref={draggleRef}>{modal}</div>
                    </Draggable>
                )}
                footer={null}
                width={"50%"}
            >
                {formItems && !modalContent ? (
                    <Form
                        name="basic"
                        form={form}
                        labelCol={{ span: 24 }}
                        style={{
                            width: "100%",
                        }}
                        wrapperCol={{ span: 24 }}
                        initialValues={{
                            remember: true,
                        }}
                        onFinish={onFinish}
                        onFinishFailed={onFinishFailed}
                        autoComplete="off"
                    >
                        {formItems}
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-evenly",
                            }}
                        >
                            <Button onClick={handleCancel}>{"Hủy"}</Button>
                            <Form.Item wrapperCol={{ offset: 6, span: 18 }}>
                                <Button
                                    type="primary"
                                    htmlType="submit"
                                    loading={loading}
                                >
                                    {submitButtonContent}
                                </Button>
                            </Form.Item>
                        </div>
                    </Form>
                ) : (
                    <></>
                )}
                {modalContent && !formItems ? (
                    <div>
                        {modalContent}
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-evenly",
                            }}
                        >
                            <Button onClick={handleCancel}>{"Hủy"}</Button>
                            <Button
                                type="primary"
                                onClick={onFinish}
                                loading={loading}
                            >
                                {submitButtonContent}
                            </Button>
                        </div>
                    </div>
                ) : (
                    <></>
                )}
            </Modal>
        </div>
    );
};

export default AddModal;
