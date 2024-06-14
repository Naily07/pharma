import { ArrowRightTwoTone, Visibility, VisibilityOff } from "@mui/icons-material";
import { Container, FormControl, IconButton, InputAdornment, InputLabel, Link, OutlinedInput } from "@mui/material";
import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import { useState, useEffect } from "react";
import logo from "../assets/logo.png";
import { useForm } from "react-hook-form";
import Button from "../components/btn/MuiButton.jsx";
import axios from "../api/axios.jsx";
import { Toaster, toast } from "sonner";

const Login = () => {
	const [showPassword, setShowPassword] = useState(false);
	const [isResponse, setResponse] = useState(false);
	const navigate = useNavigate();
	const handleClickShowPassword = () => setShowPassword((show) => !show);

	const {
		register,
		handleSubmit,
		formState: { errors },
		resetField,
	} = useForm({
		mode: "onTouched",
	});

	useEffect(() => {
		if (isResponse) {
			navigate("/dashboard");
		}
	}, [isResponse, navigate]);

	async function onSubmit(data) {
		try {
			const response = await axios.post("/login", {
				identifiant: data.identifiant,
				password: data.password,
			});

			if (response.status === 200) {
				resetField("identifiant");
				resetField("password");
				setResponse(true);
			}
		} catch (e) {
			if (e.response && e.response.status === 401) {
				toast.warning("Informations d'identification invalides");
			} else {
				toast.error("Une erreur inattendue s'est produite");
			}
			console.error(e);
		}
	}

	const handleMouseDownPassword = (event) => {
		event.preventDefault();
	};

	return (
		<>
			<Container
				maxWidth="xs"
				sx={{
					height: "100svh",
					paddingTop: 19,
				}}
			>
				<form onSubmit={handleSubmit(onSubmit)}>
					<Box
						sx={{
							display: "flex",
							justifyContent: "center",
							flexDirection: "column",
							alignItems: "center",
							bgcolor: "#fff",
							p: 5,
							borderRadius: "5px",
							gap: 2,
						}}
					>
						<img src={logo} width={220} />
						<TextField
							label="Identifiant"
							color="primary"
							fullWidth
							{...register("identifiant", {
								required: "Veuillez remplir ce champ",
							})}
							error={!!errors.identifiant}
							helperText={errors.identifiant?.message}
							sx={{
								marginTop: "20px",
							}}
						/>
						<FormControl fullWidth variant="outlined" color="primary">
							<InputLabel
								sx={{
									color: "primary.light",
									fontFamily: "Exo2-Medium",
								}}
							>
								Mot de passe
							</InputLabel>
							<OutlinedInput
								type={showPassword ? "text" : "password"}
								{...register("password", {
									required: "Veuillez remplir ce champ",
								})}
								error={!!errors.password}
								endAdornment={
									<InputAdornment position="end">
										<IconButton
											aria-label="toggle password visibility"
											onClick={handleClickShowPassword}
											onMouseDown={handleMouseDownPassword}
											edge="end"
										>
											{showPassword ? <VisibilityOff /> : <Visibility />}
										</IconButton>
									</InputAdornment>
								}
								label=" Mot de passe"
							/>
						</FormControl>
						<Button type="submit" text="Se connecter" fullWidth endIcon={<ArrowRightTwoTone />} />
						<Link
							onClick={() => navigate("/dashboard")}
							underline="always"
							color="primary"
							sx={{
								color: "primary",
								display: "block",
								alignSelf: "center",
								cursor: "pointer",
							}}
						>
							Mot de passe oublié ?
						</Link>
						<Toaster position="top-center" richColors closeButton />
					</Box>
				</form>
			</Container>
		</>
	);
};

export default Login;
