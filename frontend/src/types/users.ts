export interface IUser {
    id: string;
    username: string;
    role: string;
    createdAt: string;
    updatedAt: string;
}

export interface SignUpFormValues {
    username: string;
    email: string;
    password: string;
    retypePassword: string;
}

export interface SignUpResponse {
    username: string;
    detail?: string;
}
