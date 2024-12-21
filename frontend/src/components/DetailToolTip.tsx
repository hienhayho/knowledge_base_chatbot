import { Tooltip } from "antd";

const DetailToolTip = ({
    icon,
    title,
}: {
    icon: React.ReactNode;
    title: string;
}) => {
    return <Tooltip title={title}>{icon}</Tooltip>;
};

export default DetailToolTip;
