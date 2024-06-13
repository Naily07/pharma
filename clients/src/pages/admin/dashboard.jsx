import { Box, Stack } from "@mui/material";
import NavBar from "../../components/header.jsx";
import AdminSideBar from "./adminSideBar.jsx";
import AdminListProducts from "./adminListProducts.jsx";

const Dashboard = () => {
	return (
		<Box>
			<NavBar />
			<Stack direction="row" justifyContent="space-between" gap={3} mx="25px" mt={13}>
				<Box bgcolor="white" borderRadius={5} flex={1}>
					<AdminSideBar />
				</Box>
				<Box bgcolor="white" borderRadius={5} p={3} flex={4}>
					<AdminListProducts />
				</Box>
			</Stack>
		</Box>
	);
};
export default Dashboard;
