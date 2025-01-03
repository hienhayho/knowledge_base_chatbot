import { IUser, IUserUpdateFormValues } from "@/types";
import { Modal, message, Input, Divider } from "antd";
import DetailToolTip from "@/components/DetailToolTip";
import { useState } from "react";
import { Info } from "lucide-react";
import { adminApi } from "@/api";

const EditUserModal = ({
    icon,
    user,
    allUsers,
    setUsers,
}: {
    icon: React.ReactNode;
    user: IUser;
    allUsers: IUser[];
    setUsers: (users: IUser[]) => void;
}) => {
    const [messageApi, contextHolder] = message.useMessage();
    const [isUpdating, setIsUpdating] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const [userUpdateForm, setUserUpdateForm] = useState<IUserUpdateFormValues>(
        {
            organization: user.organization,
        }
    );

    const showModal = () => {
        setIsModalOpen(true);
    };

    const handleOk = async () => {
        try {
            setIsUpdating(true);

            await adminApi.updateUser(user.id, userUpdateForm.organization);

            messageApi.success({
                content: `Updated successfully !!!`,
                duration: 1,
            });
            setUsers(
                allUsers.map((u) =>
                    u.id === user.id
                        ? {
                              ...u,
                              organization: userUpdateForm.organization,
                          }
                        : u
                )
            );
        } catch (error) {
            const errMessage = (error as Error).message;
            console.error(error);
            messageApi.error(errMessage);
        } finally {
            setIsModalOpen(false);
            setIsUpdating(false);
        }
    };

    const handleCancel = () => {
        setIsModalOpen(false);
    };

    return (
        <div>
            {contextHolder}
            <div onClick={showModal}>{icon}</div>
            <Modal
                title={null}
                open={isModalOpen}
                onOk={handleOk}
                onCancel={handleCancel}
                confirmLoading={isUpdating}
            >
                <div className="p-4">
                    <div className="flex gap-8">
                        <div className="w-full flex flex-col">
                            <span className="flex text-blue-400 font-semibold text-lg justify-center">
                                Cập nhật thông tin
                            </span>
                            <Divider />
                            <div className="flex gap-2">
                                <label className="text-sm font-semibold text-black mb-1">
                                    Thông tin organization
                                </label>
                                <DetailToolTip
                                    title="Sẽ được đưa vào câu chào mừng lúc tạo conversation mới ==> Xin chào anh/chị. Em là nhân viên hỗ trợ của {organization}. Anh/chị cần giúp đỡ hoặc có câu hỏi gì không ạ ?"
                                    icon={<Info size={16} />}
                                />
                            </div>
                            <Input
                                size="middle"
                                placeholder="Tên trường"
                                value={userUpdateForm.organization}
                                onChange={(e) => {
                                    setUserUpdateForm((prev) => ({
                                        ...prev,
                                        organization: e.target.value,
                                    }));
                                }}
                                style={{ width: "100%" }}
                            />
                        </div>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default EditUserModal;
