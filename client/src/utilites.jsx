import axios from "axios";
import { redirect } from "react-router-dom";

export const api = axios.create({
    baseURL: "/api/v1/",
    withCredentials: true,
})



const errorMessage = (error)=>{
    const data = error.response?.data;
    if (!data) return "Could not reach the server.";
    return typeof data === "string" ? data : JSON.stringify(data);
}


// REGISTER and Login
export const userAuth = async (email, password, create)=>{
    try{
        const response = await api.post(
            create ? "users/create/" : "users/login/",
            {
                email,
                password
            }
        );
       
        return response.data.email

    }catch (error){
        alert(errorMessage(error))
        return null;
    }

}

export const userConfirmation = async () => {
    try{
        const response = await api.get("users/");
        return response.data.email;
    } catch (error){
        return null;
    }
}

export const userLogOut = async () =>{
    try{
        await api.post("users/logout/")
    }catch(error){
        console.error("Logout request failed", error)
    }

    return null

}

//  blocks a route: bounce to login page if there is no token
export const requireLogin = async ()=>{
    const email = await userConfirmation();
    if (!email) throw redirect("/");
    return email;
}

//  the reverse.... a logged in user has no business on the login page
export const redirectIfLoggedIn = async ()=>{
    const email = await userConfirmation();
    return email ? redirect("/home") : null;
}

export const homeLoader = async ()=>{
    await requireLogin()
    return getTasks()
}

export const getTasks =async()=>{
    try{
        const response = await api.get("tasks/");
        return response.data
    }catch (error){
        console.error(errorMessage(error));
        return []
    }
}

export const createTask =async (taskObj)=>{
    try{
        const response = await api.post("tasks/", taskObj)
        return response.data
    }catch(error){
        alert(errorMessage(error))
        return null
    }

}

export const updateTask = async (taskObj)=>{
    try{
        const response = await api.put(`tasks/${taskObj.id}/`, taskObj);
        return response.data;
    }catch(error){
        alert(errorMessage(error))
        return null
    }
}

export const deleteTask = async (taskId) =>{
    try{
        await api.delete(`tasks/${taskId}/`);
        return true;
    }catch(error){
        alert(errorMessage(error));
        return false;
    }
}